"""
收钱吧订单查询示例 (Python)

支持单次查询和轮询查询两种模式
"""

import hashlib
import json
import time

import requests

API_BASE = "https://vsi-api.shouqianba.com"

# 最终状态集合
FINAL_STATUSES = {"PAID", "PAY_CANCELED", "REFUNDED", "PARTIAL_REFUNDED"}


def md5_sign(body_str: str, key: str) -> str:
    """计算 MD5 签名"""
    content = body_str + key
    return hashlib.md5(content.encode("utf-8")).hexdigest()


class ShouqianbaQueryClient:
    """收钱吧查询客户端"""

    def __init__(self, terminal_sn: str, terminal_key: str):
        self.terminal_sn = terminal_sn
        self.terminal_key = terminal_key

    def _request(self, body: dict) -> dict:
        """发送查询请求"""
        body_str = json.dumps(body, ensure_ascii=False)
        sign = md5_sign(body_str, self.terminal_key)

        headers = {
            "Authorization": f"{self.terminal_sn} {sign}",
            "Content-Type": "application/json; charset=utf-8",
        }

        resp = requests.post(
            f"{API_BASE}/upay/v2/query",
            data=body_str.encode("utf-8"),
            headers=headers,
            timeout=30,
        )
        return resp.json()

    def query(self, client_sn: str = None, sn: str = None) -> dict:
        """
        查询订单

        Args:
            client_sn: 商户订单号（与 sn 二选一）
            sn: 收钱吧订单号（优先级高于 client_sn）

        Returns:
            {"order_status": ..., "data": ..., "is_final": bool}
        """
        body = {"terminal_sn": self.terminal_sn}
        if sn:
            body["sn"] = sn
        elif client_sn:
            body["client_sn"] = client_sn
        else:
            raise ValueError("sn 和 client_sn 至少传一个")

        result = self._request(body)

        if result.get("result_code") != "200":
            return {
                "order_status": "ERROR",
                "data": None,
                "is_final": False,
                "message": result.get("error_message", "通信失败"),
            }

        biz = result.get("biz_response", {})
        if biz.get("result_code") != "SUCCESS":
            return {
                "order_status": "ERROR",
                "data": None,
                "is_final": False,
                "message": f"查询失败: {biz.get('result_code')}",
            }

        data = biz.get("data", {})
        order_status = data.get("order_status", "")

        return {
            "order_status": order_status,
            "data": data,
            "is_final": order_status in FINAL_STATUSES,
            "message": "查询成功",
        }

    def poll_until_final(self, client_sn: str, max_wait_seconds: int = 120) -> dict:
        """
        轮询查询，等待最终状态

        Args:
            client_sn: 商户订单号
            max_wait_seconds: 最大等待时间（秒）

        Returns:
            最终查询结果
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            if elapsed > max_wait_seconds:
                return {
                    "order_status": "TIMEOUT",
                    "data": {"client_sn": client_sn},
                    "is_final": False,
                    "message": f"轮询超时（{max_wait_seconds}秒）",
                }

            result = self.query(client_sn=client_sn)

            if result["is_final"]:
                return result

            print(f"[{elapsed:.0f}s] 状态: {result['order_status']}，继续轮询...")

            # 轮询间隔：前60秒3秒，之后10秒
            interval = 3 if elapsed < 60 else 10
            time.sleep(interval)


if __name__ == "__main__":
    client = ShouqianbaQueryClient(
        terminal_sn="your_terminal_sn",
        terminal_key="your_terminal_key",
    )

    # 单次查询
    result = client.query(client_sn="20230615143052001")
    print(f"查询结果: {result}")

    # 轮询查询（等待支付完成）
    # result = client.poll_until_final("20230615143052001", max_wait_seconds=120)
    # print(f"最终结果: {result}")
