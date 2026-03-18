"""
收钱吧退款示例 (Python)

支持全额退款和部分退款
退款是异步操作，需查询确认最终结果
注意：所有交易都是真实的，测试支付后务必退款
"""

import hashlib
import json
import time
import uuid

import requests

API_BASE = "https://vsi-api.shouqianba.com"


def md5_sign(body_str: str, key: str) -> str:
    """计算 MD5 签名"""
    content = body_str + key
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def generate_refund_request_no() -> str:
    """生成唯一退款请求号"""
    return f"REF{int(time.time() * 1000)}{uuid.uuid4().hex[:4]}"


class ShouqianbaRefundClient:
    """收钱吧退款客户端"""

    def __init__(self, terminal_sn: str, terminal_key: str):
        self.terminal_sn = terminal_sn
        self.terminal_key = terminal_key

    def refund(
        self,
        refund_request_no: str,
        refund_amount: str,
        operator: str,
        sn: str = None,
        client_sn: str = None,
        refund_reason: str = None,
    ) -> dict:
        """
        退款

        Args:
            refund_request_no: 退款请求号（商户系统内唯一）
            refund_amount: 退款金额（分）
            operator: 操作员
            sn: 收钱吧订单号（与 client_sn 二选一）
            client_sn: 商户订单号（与 sn 二选一）
            refund_reason: 退款原因

        Returns:
            {"status": "SUCCESS/FAIL/PENDING", "data": ..., "message": ...}
        """
        if not sn and not client_sn:
            raise ValueError("sn 和 client_sn 至少传一个")

        # 1. 构建请求体
        body = {
            "terminal_sn": self.terminal_sn,
            "refund_request_no": refund_request_no,
            "refund_amount": refund_amount,
            "operator": operator,
        }
        if sn:
            body["sn"] = sn
        if client_sn:
            body["client_sn"] = client_sn
        if refund_reason:
            body["refund_reason"] = refund_reason

        body_str = json.dumps(body, ensure_ascii=False)

        # 2. 计算签名
        sign = md5_sign(body_str, self.terminal_key)

        # 3. 发送退款请求
        headers = {
            "Authorization": f"{self.terminal_sn} {sign}",
            "Content-Type": "application/json; charset=utf-8",
        }

        resp = requests.post(
            f"{API_BASE}/upay/v2/refund",
            data=body_str.encode("utf-8"),
            headers=headers,
            timeout=30,
        )
        result = resp.json()

        return self._parse_response(result)

    def _parse_response(self, result: dict) -> dict:
        """解析退款响应"""
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
        if biz_code == "REFUND_SUCCESS":
            data = biz.get("data", {})
            return {
                "status": "SUCCESS",
                "data": data,
                "message": f"退款成功，订单状态: {data.get('order_status')}",
            }
        elif biz_code == "REFUND_FAIL":
            return {
                "status": "FAIL",
                "data": None,
                "message": f"退款失败: {biz.get('error_message')}",
            }
        elif biz_code in ("REFUND_IN_PROGRESS", "REFUND_FAIL_ERROR"):
            return {
                "status": "PENDING",
                "data": None,
                "message": "退款处理中，请查询确认",
            }
        else:
            return {
                "status": "FAIL",
                "data": None,
                "message": f"未知状态: {biz_code}",
            }


if __name__ == "__main__":
    client = ShouqianbaRefundClient(
        terminal_sn="your_terminal_sn",
        terminal_key="your_terminal_key",
    )

    # 全额退款
    refund_request_no = generate_refund_request_no()
    result = client.refund(
        refund_request_no=refund_request_no,
        refund_amount="100",           # 退款金额（分）
        operator="cashier_01",
        sn="7892840250140845",         # 收钱吧订单号
        refund_reason="顾客要求退款",
    )

    print(f"退款结果: {result}")

    # 部分退款
    # result = client.refund(
    #     refund_request_no=generate_refund_request_no(),
    #     refund_amount="50",  # 退50分
    #     operator="cashier_01",
    #     sn="7892840250140845",
    # )
