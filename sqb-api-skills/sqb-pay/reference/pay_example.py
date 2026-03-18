"""
收钱吧 B扫C 付款码支付示例 (Python)

核心流程：扫码 → 支付 → 轮询查询 → 确认结果
注意：所有交易都是真实的（无沙盒环境），测试后务必退款
"""

import hashlib
import json
import time
import uuid
from datetime import datetime

import requests

API_BASE = "https://vsi-api.shouqianba.com"


def md5_sign(body_str: str, key: str) -> str:
    """计算 MD5 签名"""
    content = body_str + key
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def generate_client_sn(store_id: str = "STORE01") -> str:
    """生成唯一订单号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]
    return f"{store_id}{timestamp}{uuid.uuid4().hex[:4]}"


class ShouqianbaPayClient:
    """收钱吧支付客户端"""

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

    def pay(
        self,
        client_sn: str,
        total_amount: str,
        dynamic_id: str,
        subject: str,
        operator: str,
        **kwargs,
    ) -> dict:
        """
        付款码支付

        Args:
            client_sn: 商户唯一订单号
            total_amount: 金额（单位：分）
            dynamic_id: 顾客付款码（扫码枪获取）
            subject: 交易简介（显示在顾客账单）
            operator: 操作员

        Returns:
            {"status": "SUCCESS/FAIL/PENDING", "data": ..., "message": ...}
        """
        body = {
            "terminal_sn": self.terminal_sn,
            "client_sn": client_sn,
            "total_amount": total_amount,
            "dynamic_id": dynamic_id,
            "subject": subject,
            "operator": operator,
            **kwargs,
        }

        result = self._request("/upay/v2/pay", body)
        return self._parse_pay_response(result, client_sn)

    def _parse_pay_response(self, result: dict, client_sn: str) -> dict:
        """三层状态判定"""
        # 第一层：通信层
        if result.get("result_code") != "200":
            return {
                "status": "FAIL",
                "data": None,
                "message": f"通信失败: {result.get('error_message')}",
            }

        biz = result.get("biz_response", {})
        biz_code = biz.get("result_code", "")

        # 第二层：业务层
        if biz_code == "PAY_FAIL":
            return {"status": "FAIL", "data": None, "message": "支付失败"}
        if biz_code in ("PAY_IN_PROGRESS", "PAY_FAIL_ERROR"):
            return {"status": "PENDING", "data": {"client_sn": client_sn}, "message": "支付处理中"}

        # 第三层：订单状态
        data = biz.get("data", {})
        order_status = data.get("order_status", "")

        if order_status == "PAID":
            return {"status": "SUCCESS", "data": data, "message": "支付成功"}
        elif order_status == "PAY_CANCELED":
            return {"status": "FAIL", "data": data, "message": "支付已撤销"}
        else:
            # CREATED, PAY_ERROR 等非最终状态
            return {"status": "PENDING", "data": data, "message": f"状态: {order_status}"}

    def query(self, client_sn: str = None, sn: str = None) -> dict:
        """查询订单"""
        body = {"terminal_sn": self.terminal_sn}
        if sn:
            body["sn"] = sn
        elif client_sn:
            body["client_sn"] = client_sn
        return self._request("/upay/v2/query", body)

    def pay_with_polling(
        self,
        client_sn: str,
        total_amount: str,
        dynamic_id: str,
        subject: str,
        operator: str,
        max_wait_seconds: int = 120,
        **kwargs,
    ) -> dict:
        """
        带轮询的完整支付流程

        Returns:
            {"status": "SUCCESS/FAIL/TIMEOUT", "data": ..., "message": ...}
        """
        # 1. 发起支付
        result = self.pay(client_sn, total_amount, dynamic_id, subject, operator, **kwargs)

        # 2. 最终状态直接返回
        if result["status"] != "PENDING":
            return result

        # 3. 轮询查询
        print("支付处理中，启动轮询查询...")
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            # 超时退出
            if elapsed > max_wait_seconds:
                print(f"轮询超时（{max_wait_seconds}秒），请人工确认订单状态")
                return {"status": "TIMEOUT", "data": {"client_sn": client_sn}, "message": "轮询超时"}

            # 轮询间隔：前60秒3秒，之后10秒
            interval = 3 if elapsed < 60 else 10
            time.sleep(interval)

            # 查询订单
            query_result = self.query(client_sn=client_sn)
            if query_result.get("result_code") != "200":
                print(f"查询失败，继续重试...")
                continue

            order_status = query_result.get("biz_response", {}).get("data", {}).get("order_status", "")
            print(f"[{elapsed:.0f}s] 订单状态: {order_status}")

            # 最终状态判定
            if order_status == "PAID":
                data = query_result["biz_response"]["data"]
                return {"status": "SUCCESS", "data": data, "message": "支付成功"}
            elif order_status == "PAY_CANCELED":
                return {"status": "FAIL", "data": None, "message": "支付已撤销"}
            # 其他状态继续轮询


if __name__ == "__main__":
    client = ShouqianbaPayClient(
        terminal_sn="your_terminal_sn",
        terminal_key="your_terminal_key",
    )

    # 生成唯一订单号
    client_sn = generate_client_sn("STORE01")

    # 发起支付（带轮询）
    # 注意：这是真实交易！测试后请务必退款
    result = client.pay_with_polling(
        client_sn=client_sn,
        total_amount="1",                  # 1分钱（测试用）
        dynamic_id="130818341921600584",   # 付款码（扫码枪获取）
        subject="测试商品",                 # 账单显示
        operator="cashier_01",             # 操作员
    )

    print(f"\n支付结果: {result}")
