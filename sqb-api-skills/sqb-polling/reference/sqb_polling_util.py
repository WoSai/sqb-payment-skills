"""
收钱吧轮询框架

⚠️ 重要：不同交易场景使用不同的轮询参数，不要硬编码轮询间隔。

参数化轮询策略：
  pay（B扫C 付款码支付）：前 60s 每 3s，之后每 10s，总超时 120s
  precreate（C扫B 预下单）：前 30s 每 2s，之后每 5s，总超时 240s

超时后返回 TIMEOUT 状态，由调用方决定是否继续等待或发起撤单。
"""

import time
from dataclasses import dataclass
from typing import Callable, Optional

from sqb_status_util import ParsedResponse, is_final_status, parse_response


@dataclass
class PollingConfig:
    """轮询策略配置"""
    phase1_duration: int   # 第一阶段持续时间（秒）
    phase1_interval: int   # 第一阶段轮询间隔（秒）
    phase2_interval: int   # 第二阶段轮询间隔（秒）
    max_timeout: int       # 总超时时间（秒）


# 预定义的轮询策略
PAY_POLLING_CONFIG = PollingConfig(
    phase1_duration=60,
    phase1_interval=3,
    phase2_interval=10,
    max_timeout=120,
)

PRECREATE_POLLING_CONFIG = PollingConfig(
    phase1_duration=30,
    phase1_interval=2,
    phase2_interval=5,
    max_timeout=240,
)


@dataclass
class PollingResult:
    """轮询结果"""
    status: str              # SUCCESS / FAIL / TIMEOUT
    parsed: Optional[ParsedResponse]  # 最终解析结果（TIMEOUT 时为 None）
    elapsed_seconds: float   # 实际耗时
    poll_count: int          # 轮询次数
    message: str             # 人类可读描述


def poll_until_final(
    query_fn: Callable[[], dict],
    config: PollingConfig = PAY_POLLING_CONFIG,
    on_poll: Optional[Callable[[int, float, str], None]] = None,
) -> PollingResult:
    """
    参数化轮询框架：按配置的策略反复查询，直到获得最终状态或超时。

    Args:
        query_fn: 查询函数，无参调用，返回收钱吧 API 的原始 JSON 响应字典
        config: 轮询策略配置
        on_poll: 轮询回调（poll_count, elapsed_seconds, current_status）

    Returns:
        PollingResult 包含最终状态或超时信息

    Example:
        # B扫C 付款码支付轮询
        result = poll_until_final(
            query_fn=lambda: client.query(client_sn="ORDER001"),
            config=PAY_POLLING_CONFIG,
        )

        # C扫B 预下单轮询
        result = poll_until_final(
            query_fn=lambda: client.query(client_sn="ORDER002"),
            config=PRECREATE_POLLING_CONFIG,
        )
    """
    start_time = time.time()
    poll_count = 0

    while True:
        elapsed = time.time() - start_time

        # 超时检查
        if elapsed > config.max_timeout:
            return PollingResult(
                status="TIMEOUT",
                parsed=None,
                elapsed_seconds=elapsed,
                poll_count=poll_count,
                message=f"轮询超时（{config.max_timeout}秒），请人工确认订单状态或发起撤单",
            )

        # 计算当前阶段的轮询间隔
        interval = config.phase1_interval if elapsed < config.phase1_duration else config.phase2_interval
        time.sleep(interval)

        # 执行查询
        poll_count += 1
        try:
            raw_response = query_fn()
        except Exception as e:
            # 查询失败不中断轮询，继续重试
            if on_poll:
                on_poll(poll_count, time.time() - start_time, f"查询异常: {e}")
            continue

        # 解析响应
        parsed = parse_response(raw_response)

        # 回调通知
        if on_poll:
            on_poll(poll_count, time.time() - start_time, parsed.order_status or parsed.message)

        # 检查是否为最终状态
        if parsed.is_final:
            return PollingResult(
                status=parsed.status,
                parsed=parsed,
                elapsed_seconds=time.time() - start_time,
                poll_count=poll_count,
                message=parsed.message,
            )
