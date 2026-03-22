"""
收钱吧撤单（冲正）示例 (Python)

⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易
撤单操作不可逆，请谨慎使用！

核心流程：撤单 → 判定结果 → 失败则查询确认
限制：仅限当天订单（当日 00:00 后的交易），全额撤销，已部分退款的订单不能撤单
"""

import hashlib
import json
import time

import requests

API_BASE = "https://vsi-api.shouqianba.com"


def md5_sign(body_str: str, key: str) -> str:
    """
    计算 MD5 签名
    签名逻辑参考 shared-reference/SqbSignUtil
    """
    content = body_str + key
    return hashlib.md5(content.encode("utf-8")).hexdigest()


class ShouqianbaCancelClient:
    """
    收钱吧撤单客户端

    ⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易
    """

    def __init__(self, terminal_sn: str, terminal_key: str):
        self.terminal_sn = terminal_sn
        self.terminal_key = terminal_key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json; charset=utf-8",
        })

    def _request(self, endpoint: str, body: dict) -> dict:
        """发送签名请求（签名逻辑参考 shared-reference/SqbSignUtil）"""
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

    def cancel(self, sn: str = None, client_sn: str = None) -> dict:
        """
        撤单（冲正）

        ⚠️ 警告：此操作将发起真实撤单，不可逆！
        ⚠️ 仅限当天订单（当日 00:00 后的交易），全额撤销
        ⚠️ 已部分退款的订单不能撤单

        Args:
            sn: 收钱吧订单号（sn 和 client_sn 二选一，推荐优先使用 sn）
            client_sn: 商户订单号（sn 和 client_sn 二选一）

        Returns:
            {"status": "SUCCESS/FAIL/UNCERTAIN", "data": ..., "message": ...}
        """
        if not sn and not client_sn:
            raise ValueError("sn 和 client_sn 必须至少提供一个")

        body = {"terminal_sn": self.terminal_sn}
        if sn:
            body["sn"] = sn
        if client_sn:
            body["client_sn"] = client_sn

        result = self._request("/upay/v2/cancel", body)
        return self._parse_cancel_response(result)

    def _parse_cancel_response(self, result: dict) -> dict:
        """
        撤单结果判定

        业务结果码：
        - CANCEL_SUCCESS: 撤销成功
        - CANCEL_ERROR: 撤销失败（不确定），需查询确认
        - CANCEL_ABORT_SUCCESS: 中断支付成功
        - CANCEL_ABORT_ERROR: 中断支付失败，需查询确认
        """
        # 第一层：通信层
        if result.get("result_code") != "200":
            return {
                "status": "FAIL",
                "data": None,
                "message": f"通信失败: {result.get('error_message', '未知错误')}",
            }

        biz = result.get("biz_response", {})
        biz_code = biz.get("result_code", "")
        data = biz.get("data")

        # 第二层：业务层 — 撤单结果判定
        if biz_code == "CANCEL_SUCCESS":
            return {
                "status": "SUCCESS",
                "data": data,
                "message": "撤单成功，交易已撤销，资金已退回",
            }
        elif biz_code == "CANCEL_ABORT_SUCCESS":
            return {
                "status": "SUCCESS",
                "data": data,
                "message": "中断支付成功，支付中的订单已被中断",
            }
        elif biz_code == "CANCEL_ERROR":
            # ⚠️ 不确定状态，必须查询确认！
            return {
                "status": "UNCERTAIN",
                "data": data,
                "message": "撤单结果不确定（CANCEL_ERROR），必须调用查询接口确认订单最终状态",
            }
        elif biz_code == "CANCEL_ABORT_ERROR":
            # ⚠️ 不确定状态，必须查询确认！
            return {
                "status": "UNCERTAIN",
                "data": data,
                "message": "中断支付结果不确定（CANCEL_ABORT_ERROR），必须调用查询接口确认订单最终状态",
            }
        else:
            return {
                "status": "FAIL",
                "data": data,
                "message": f"撤单失败: {biz.get('error_message', biz_code)}",
            }

    def query(self, sn: str = None, client_sn: str = None) -> dict:
        """
        查询订单状态（用于撤单结果不确定时确认）

        Args:
            sn: 收钱吧订单号
            client_sn: 商户订单号
        """
        body = {"terminal_sn": self.terminal_sn}
        if sn:
            body["sn"] = sn
        elif client_sn:
            body["client_sn"] = client_sn
        return self._request("/upay/v2/query", body)

    def cancel_with_retry(
        self,
        sn: str = None,
        client_sn: str = None,
        max_query_attempts: int = 6,
        query_interval: int = 5,
    ) -> dict:
        """
        带查询确认的完整撤单流程

        ⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易

        流程：
        1. 发起撤单请求
        2. 若撤单成功（CANCEL_SUCCESS / CANCEL_ABORT_SUCCESS），直接返回
        3. 若撤单结果不确定（CANCEL_ERROR / CANCEL_ABORT_ERROR），查询订单确认
        4. 查询确认订单最终状态

        Args:
            sn: 收钱吧订单号（sn 和 client_sn 二选一）
            client_sn: 商户订单号（sn 和 client_sn 二选一）
            max_query_attempts: 最大查询次数，默认 6 次
            query_interval: 查询间隔（秒），默认 5 秒

        Returns:
            {"status": "SUCCESS/FAIL/UNCERTAIN", "data": ..., "message": ...}
        """
        # 1. 发起撤单
        print("发起撤单请求...")
        cancel_result = self.cancel(sn=sn, client_sn=client_sn)

        # 2. 撤单成功，直接返回
        if cancel_result["status"] == "SUCCESS":
            print(f"撤单成功: {cancel_result['message']}")
            return cancel_result

        # 3. 撤单明确失败，直接返回
        if cancel_result["status"] == "FAIL":
            print(f"撤单失败: {cancel_result['message']}")
            return cancel_result

        # 4. 撤单结果不确定（CANCEL_ERROR / CANCEL_ABORT_ERROR），启动查询确认
        print(f"撤单结果不确定: {cancel_result['message']}")
        print("启动查询确认流程...")

        for attempt in range(1, max_query_attempts + 1):
            time.sleep(query_interval)

            print(f"[第 {attempt}/{max_query_attempts} 次查询]")

            try:
                query_result = self.query(sn=sn, client_sn=client_sn)
            except Exception as e:
                print(f"查询异常: {e}，继续重试...")
                continue

            if query_result.get("result_code") != "200":
                print(f"查询通信失败，继续重试...")
                continue

            order_status = (
                query_result.get("biz_response", {})
                .get("data", {})
                .get("order_status", "")
            )
            print(f"订单状态: {order_status}")

            # 判断最终状态
            if order_status == "PAY_CANCELED":
                data = query_result["biz_response"]["data"]
                return {
                    "status": "SUCCESS",
                    "data": data,
                    "message": "查询确认：撤单已生效，订单已取消",
                }
            elif order_status == "PAID":
                data = query_result["biz_response"]["data"]
                return {
                    "status": "FAIL",
                    "data": data,
                    "message": "查询确认：撤单未生效，订单仍为已支付状态（可重新发起撤单或退款）",
                }
            # 其他状态继续查询

        # 查询多次仍无法确认
        print(f"查询 {max_query_attempts} 次后仍无法确认订单状态，建议人工介入处理")
        return {
            "status": "UNCERTAIN",
            "data": cancel_result.get("data"),
            "message": f"查询 {max_query_attempts} 次后仍无法确认订单最终状态，建议人工介入处理",
        }


if __name__ == "__main__":
    # ⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易！
    # ⚠️ 仅限当天订单（当日 00:00 后的交易）
    # ⚠️ 撤单为全额撤销，已部分退款的订单不能撤单

    client = ShouqianbaCancelClient(
        terminal_sn="your_terminal_sn",
        terminal_key="your_terminal_key",
    )

    # 场景1：使用收钱吧订单号撤单（推荐）
    result = client.cancel_with_retry(sn="7892840250140845")
    print(f"\n撤单结果: {result}")

    # 场景2：使用商户订单号撤单
    # result = client.cancel_with_retry(client_sn="20230615143052001")
    # print(f"\n撤单结果: {result}")

    # 场景3：pay 接口超时后立即撤单保障资金安全
    # pay_client_sn = "ORDER_THAT_TIMED_OUT"
    # result = client.cancel_with_retry(client_sn=pay_client_sn)
    # if result["status"] == "SUCCESS":
    #     print("撤单成功，资金安全")
    # elif result["status"] == "FAIL":
    #     print("撤单失败，订单仍为已支付状态，请确认是否需要退款")
    # else:
    #     print("撤单状态不确定，请人工确认")
