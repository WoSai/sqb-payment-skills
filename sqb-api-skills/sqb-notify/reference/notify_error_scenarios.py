"""
sqb-notify 异常路径参考（Python）

示例覆盖：
- 验签失败直接拒绝
- 重复回调幂等去重
- 回调乱序保护（状态只前进不回退）
"""

from dataclasses import dataclass
from typing import Set


@dataclass
class NotifyPayload:
    client_sn: str
    status: str
    sign_valid: bool
    version: int  # 状态版本，越大越新


class NotifyHandler:
    def __init__(self) -> None:
        self.processed_keys: Set[str] = set()
        self.latest_version: dict[str, int] = {}

    def handle(self, payload: NotifyPayload) -> str:
        # 1) 验签失败：拒绝处理
        if not payload.sign_valid:
            return "reject"

        # 2) 幂等去重：同 client_sn 只处理一次
        if payload.client_sn in self.processed_keys:
            return "success"

        # 3) 乱序保护：旧版本状态不能覆盖新版本
        current = self.latest_version.get(payload.client_sn, -1)
        if payload.version < current:
            return "success"

        # 4) 处理并标记
        self.latest_version[payload.client_sn] = payload.version
        self.processed_keys.add(payload.client_sn)
        return "success"
