"""
收钱吧 C扫B 预下单支付示例 (Python)

核心流程：预下单 → 获取二维码 → 顾客扫码 → 轮询查询 → 确认结果

⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易
测试后务必通过退款接口进行退款清理
"""

import hashlib
import json
import time
import uuid
from datetime import datetime

import requests

API_BASE = "https://vsi-api.shouqianba.com"

# 轮询策略配置（对应 shared-reference/SqbPollingUtil 的 PRECREATE_POLLING_CONFIG）
PHASE1_DURATION = 30    # 第一阶段持续时间（秒）
PHASE1_INTERVAL = 2     # 第一阶段轮询间隔（秒）
PHASE2_INTERVAL = 5     # 第二阶段轮询间隔（秒）
MAX_TIMEOUT = 240       # 总超时时间（秒），预下单二维码约4分钟过期

# 支付渠道
PAYWAY_ALIPAY = "1"
PAYWAY_WECHAT = "3"


def md5_sign(body_str: str, key: str) -> str:
    """计算 MD5 签名（参考 shared-reference/SqbSignUtil）"""
    content = body_str + key
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def generate_client_sn(store_id: str = "STORE01") -> str:
    """生成唯一订单号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]
    return f"{store_id}{timestamp}{uuid.uuid4().hex[:4]}"


class ShouqianbaPreCreateClient:
    """收钱吧 C扫B 预下单客户端"""

    def __init__(self, terminal_sn: str, terminal_key: str):
        self.terminal_sn = terminal_sn
        self.terminal_key = terminal_key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json; charset=utf-8",
        })

    def _request(self, endpoint: str, body: dict) -> dict:
        """发送签名请求"""
        body_str = json.dumps(body, ensure_ascii=False)
        sign = md5_sign(body_str, self.terminal_key)

        headers = {
            "Authorization": f"{self.terminal_sn} {sign}",
        }

        resp = self.session.post(
            f"{API_BASE}{endpoint}",
            data=body_str.encode("utf-8"),
            headers=headers,
            timeout=30,
        )
        return resp.json()

    def precreate(
        self,
        client_sn: str,
        total_amount: str,
        payway: str,
        subject: str,
        operator: str,
        **kwargs,
    ) -> dict:
        """
        C扫B 预下单

        Args:
            client_sn: 商户唯一订单号
            total_amount: 金额（单位：分）
            payway: 支付方式（1=支付宝, 3=微信）— 预下单必填
            subject: 交易简介（显示在顾客账单）
            operator: 操作员

        Returns:
            {"status": "SUCCESS/FAIL/PENDING", "qr_code": ..., "data": ..., "message": ...}
        """
        # payway 必填校验
        if not payway or payway not in ("1", "3"):
            raise ValueError("预下单必须指定 payway（1=支付宝, 3=微信）")

        body = {
            "terminal_sn": self.terminal_sn,
            "client_sn": client_sn,
            "total_amount": total_amount,
            "payway": payway,
            "subject": subject,
            "operator": operator,
            **kwargs,
        }

        result = self._request("/upay/v2/precreate", body)
        return self._parse_precreate_response(result, client_sn)

    def _parse_precreate_response(self, result: dict, client_sn: str) -> dict:
        """
        三层状态判定（参考 shared-reference/SqbStatusUtil）
        """
        # 第一层：通信层
        if result.get("result_code") != "200":
            return {
                "status": "FAIL",
                "qr_code": None,
                "data": None,
                "message": f"通信失败: {result.get('error_message')}",
            }

        biz = result.get("biz_response", {})
        biz_code = biz.get("result_code", "")

        # 第二层：业务层
        if biz_code == "PRECREATE_FAIL":
            return {"status": "FAIL", "qr_code": None, "data": None, "message": "预下单失败"}
        if biz_code in ("PRECREATE_IN_PROGRESS", "PRECREATE_FAIL_ERROR"):
            return {
                "status": "PENDING",
                "qr_code": None,
                "data": {"client_sn": client_sn},
                "message": "预下单处理中",
            }

        # 第三层：订单状态
        data = biz.get("data", {})
        order_status = data.get("order_status", "")
        qr_code = data.get("qr_code")

        if order_status == "PAID":
            return {"status": "SUCCESS", "qr_code": None, "data": data, "message": "支付成功"}
        elif order_status == "PAY_CANCELED":
            return {"status": "FAIL", "qr_code": None, "data": data, "message": "支付已撤销"}
        else:
            # IN_QUEUE, CREATED 等非最终状态 — 提取 qr_code 供前端渲染
            # ⚠️ 前端需要将 qr_code 字段渲染为二维码图片供顾客扫码
            return {
                "status": "PENDING",
                "qr_code": qr_code,
                "data": data,
                "message": f"预下单成功，状态: {order_status}，请将 qr_code 渲染为二维码",
            }

    def query(self, client_sn: str = None, sn: str = None) -> dict:
        """查询订单"""
        body = {"terminal_sn": self.terminal_sn}
        if sn:
            body["sn"] = sn
        elif client_sn:
            body["client_sn"] = client_sn
        return self._request("/upay/v2/query", body)

    def precreate_with_polling(
        self,
        client_sn: str,
        total_amount: str,
        payway: str,
        subject: str,
        operator: str,
        max_wait_seconds: int = MAX_TIMEOUT,
        **kwargs,
    ) -> dict:
        """
        带轮询的完整预下单支付流程

        轮询策略（对应 shared-reference/SqbPollingUtil 的 PRECREATE_POLLING_CONFIG）：
          - 前 30 秒每 2 秒查询一次
          - 之后每 5 秒查询一次
          - 预下单订单约 4 分钟（240 秒）后自动过期

        Returns:
            {"status": "SUCCESS/FAIL/TIMEOUT", "qr_code": ..., "data": ..., "message": ...}
        """
        # 1. 发起预下单
        result = self.precreate(client_sn, total_amount, payway, subject, operator, **kwargs)

        # 2. 最终状态直接返回
        if result["status"] != "PENDING":
            return result

        # 展示二维码信息
        if result.get("qr_code"):
            print(f"二维码内容: {result['qr_code']}")
            print("⚠️ 前端需要将 qr_code 渲染为二维码图片供顾客扫码")

        # 3. 轮询查询（使用 PRECREATE_POLLING_CONFIG 策略）
        print("等待顾客扫码支付，启动轮询查询...")
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            # 超时退出
            if elapsed > max_wait_seconds:
                print(f"轮询超时（{max_wait_seconds}秒），预下单二维码已过期，请人工确认订单状态")
                return {
                    "status": "TIMEOUT",
                    "qr_code": None,
                    "data": {"client_sn": client_sn},
                    "message": "轮询超时，二维码已过期",
                }

            # 轮询间隔：前30秒2秒，之后5秒
            interval = PHASE1_INTERVAL if elapsed < PHASE1_DURATION else PHASE2_INTERVAL
            time.sleep(interval)

            # 查询订单
            query_result = self.query(client_sn=client_sn)
            if query_result.get("result_code") != "200":
                print("查询失败，继续重试...")
                continue

            order_status = query_result.get("biz_response", {}).get("data", {}).get("order_status", "")
            print(f"[{elapsed:.0f}s] 订单状态: {order_status}")

            # 最终状态判定
            if order_status == "PAID":
                data = query_result["biz_response"]["data"]
                return {"status": "SUCCESS", "qr_code": None, "data": data, "message": "支付成功"}
            elif order_status == "PAY_CANCELED":
                return {"status": "FAIL", "qr_code": None, "data": None, "message": "支付已撤销"}
            # 其他状态（IN_QUEUE, CREATED 等）继续轮询


if __name__ == "__main__":
    # ⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易
    # 测试后请务必通过退款接口清理测试订单

    client = ShouqianbaPreCreateClient(
        terminal_sn="your_terminal_sn",
        terminal_key="your_terminal_key",
    )

    # 生成唯一订单号
    client_sn = generate_client_sn("STORE01")

    # 发起预下单（带轮询）
    # 注意：这是真实交易！测试后请务必退款
    result = client.precreate_with_polling(
        client_sn=client_sn,
        total_amount="1",           # 1分钱（测试用）
        payway=PAYWAY_WECHAT,       # 微信支付（3）
        subject="测试商品",          # 账单显示
        operator="cashier_01",      # 操作员
    )

    print(f"\n支付结果: {result}")

    # ⚠️ 测试完成后，请使用退款接口退款：
    # POST /upay/v2/refund
    # 参考 sqb-refund skill
