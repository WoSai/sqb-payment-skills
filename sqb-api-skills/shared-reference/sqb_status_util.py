"""
收钱吧三层状态判定工具

⚠️ 重要：所有交易类 skill 共享此状态判定实现，不要自行重新实现判定逻辑。

三层判定模型：
  第一层 result_code        → 通信层（200=成功，其他=通信失败）
  第二层 biz_response.result_code → 业务层（PAY_SUCCESS/PAY_FAIL 等）
  第三层 order_status       → 订单最终状态（PAID/PAY_CANCELED 等）

最终状态（不可变）：PAID, PAY_CANCELED, REFUNDED, PARTIAL_REFUNDED, CANCELED
非最终状态（需轮询）：CREATED, PAY_ERROR, REFUND_ERROR, CANCEL_ERROR
"""

from dataclasses import dataclass
from typing import Any, Optional

# 最终状态集合——收到这些状态后可以停止轮询
FINAL_ORDER_STATUSES = frozenset({
    "PAID",
    "PAY_CANCELED",
    "REFUNDED",
    "PARTIAL_REFUNDED",
    "CANCELED",
})

# 业务层成功码映射
BIZ_SUCCESS_CODES = frozenset({
    "PAY_SUCCESS",
    "PRECREATE_SUCCESS",
    "REFUND_SUCCESS",
    "CANCEL_SUCCESS",
    "CANCEL_ABORT_SUCCESS",
    "SUCCESS",
})

# 业务层确定失败码（不需要轮询）
BIZ_DEFINITE_FAIL_CODES = frozenset({
    "PAY_FAIL",
    "PRECREATE_FAIL",
    "REFUND_FAIL",
    "CANCEL_ABORT_ERROR",
    "FAIL",
})

# 业务层不确定失败码（需要轮询确认）
BIZ_UNCERTAIN_CODES = frozenset({
    "PAY_FAIL_ERROR",
    "PAY_IN_PROGRESS",
    "REFUND_IN_PROGRESS",
    "REFUND_FAIL_ERROR",
    "CANCEL_ERROR",
})


@dataclass
class ParsedResponse:
    """统一的响应解析结果"""
    status: str          # SUCCESS / FAIL / PENDING
    order_status: str    # 原始 order_status 值
    sn: str              # 收钱吧订单号
    client_sn: str       # 商户订单号
    data: Optional[dict] # 完整的 data 节点
    message: str         # 人类可读的状态描述
    is_final: bool       # 是否为最终状态（可停止轮询）
    raw: dict            # 原始完整响应


def is_final_status(order_status: str) -> bool:
    """判断 order_status 是否为最终状态"""
    return order_status in FINAL_ORDER_STATUSES


def parse_response(response: dict) -> ParsedResponse:
    """
    三层状态判定：解析收钱吧 API 响应

    Args:
        response: 收钱吧 API 的完整 JSON 响应

    Returns:
        ParsedResponse 结构化结果
    """
    # ── 第一层：通信层 ──
    result_code = response.get("result_code", "")
    if result_code != "200":
        error_code = response.get("error_code", "UNKNOWN")
        error_msg = response.get("error_message", "通信失败")
        return ParsedResponse(
            status="FAIL",
            order_status="",
            sn="",
            client_sn="",
            data=None,
            message=f"通信失败[{error_code}]: {error_msg}",
            is_final=True,
            raw=response,
        )

    # ── 第二层：业务层 ──
    biz = response.get("biz_response", {})
    biz_code = biz.get("result_code", "")

    if biz_code in BIZ_DEFINITE_FAIL_CODES:
        error_msg = biz.get("error_message", biz_code)
        return ParsedResponse(
            status="FAIL",
            order_status="",
            sn="",
            client_sn="",
            data=None,
            message=f"业务失败: {error_msg}",
            is_final=True,
            raw=response,
        )

    if biz_code in BIZ_UNCERTAIN_CODES:
        return ParsedResponse(
            status="PENDING",
            order_status="",
            sn="",
            client_sn="",
            data=None,
            message=f"状态不确定[{biz_code}]，需轮询查询",
            is_final=False,
            raw=response,
        )

    # ── 第三层：订单状态 ──
    data = biz.get("data", {})
    order_status = data.get("order_status", "")
    sn = data.get("sn", "")
    client_sn = data.get("client_sn", "")

    if order_status == "PAID":
        return ParsedResponse("SUCCESS", order_status, sn, client_sn, data, "支付成功", True, response)
    elif order_status == "PAY_CANCELED":
        return ParsedResponse("FAIL", order_status, sn, client_sn, data, "支付已撤销", True, response)
    elif order_status == "REFUNDED":
        return ParsedResponse("SUCCESS", order_status, sn, client_sn, data, "全额退款成功", True, response)
    elif order_status == "PARTIAL_REFUNDED":
        return ParsedResponse("SUCCESS", order_status, sn, client_sn, data, "部分退款成功", True, response)
    elif order_status == "CANCELED":
        return ParsedResponse("SUCCESS", order_status, sn, client_sn, data, "订单已撤销", True, response)
    else:
        # CREATED, PAY_ERROR, REFUND_ERROR, CANCEL_ERROR 等非最终状态
        return ParsedResponse("PENDING", order_status, sn, client_sn, data, f"状态: {order_status}，需继续轮询", False, response)
