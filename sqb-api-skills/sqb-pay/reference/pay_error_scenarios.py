"""
sqb-pay 异常路径参考（Python）

说明：
- 本文件用于补齐“正常路径之外”的参考实现，便于新项目试点时做异常联调。
- 示例重点：超时重试、非最终状态轮询超时、金额不一致保护。
"""

from dataclasses import dataclass
from typing import Callable, Optional
import time


@dataclass
class PayOutcome:
    status: str  # SUCCESS / FAIL / PENDING / TIMEOUT
    message: str
    order_sn: Optional[str] = None


def run_with_timeout_retry(
    request_fn: Callable[[], PayOutcome],
    max_retry: int = 2,
) -> PayOutcome:
    """网络抖动/超时时做有限重试，避免直接失败。"""
    last_err = None
    for _ in range(max_retry + 1):
        try:
            return request_fn()
        except TimeoutError as exc:
            last_err = exc
    return PayOutcome(status="PENDING", message=f"request timeout: {last_err}")


def poll_until_final(
    query_fn: Callable[[], str],
    max_wait_seconds: int = 120,
) -> PayOutcome:
    """非最终状态轮询：超时后返回 TIMEOUT 并要求人工确认。"""
    start = time.time()
    while time.time() - start < max_wait_seconds:
        order_status = query_fn()
        if order_status == "PAID":
            return PayOutcome(status="SUCCESS", message="paid")
        if order_status == "PAY_CANCELED":
            return PayOutcome(status="FAIL", message="canceled")
        time.sleep(1)
    return PayOutcome(status="TIMEOUT", message="query timeout, manual confirm required")


def guard_amount_consistency(local_amount_fen: int, channel_amount_fen: int) -> None:
    """金额不一致必须阻断自动完成，进入人工复核。"""
    if local_amount_fen != channel_amount_fen:
        raise ValueError(
            f"amount mismatch local={local_amount_fen}, channel={channel_amount_fen}"
        )
