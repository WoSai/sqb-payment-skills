"""
收钱吧签名工具类

⚠️ 重要：所有交易类 skill 共享此签名实现，不要自行编写签名逻辑。

签名算法：MD5(request_body + key)
- request_body 必须是 UTF-8 编码的原始 JSON 字符串
- 签名时的字符串必须和实际发送的请求体完全一致（包括字段顺序、空格等）
- MD5 输出为 32 位小写十六进制字符串
- Authorization 头格式：{sn} {sign}（sn 和 sign 之间有且仅有一个空格）
"""

import hashlib
import json
from typing import Any


def md5_sign(body_str: str, key: str) -> str:
    """
    计算收钱吧 MD5 签名

    Args:
        body_str: 请求体的原始 JSON 字符串（UTF-8）
        key: 密钥（vendor_key 或 terminal_key）

    Returns:
        32 位小写十六进制 MD5 签名字符串
    """
    sign_content = body_str + key
    return hashlib.md5(sign_content.encode("utf-8")).hexdigest()


def build_authorization(sn: str, body_str: str, key: str) -> str:
    """
    构建 Authorization 请求头

    Args:
        sn: 序列号（vendor_sn 或 terminal_sn）
        body_str: 请求体的原始 JSON 字符串
        key: 密钥（vendor_key 或 terminal_key）

    Returns:
        Authorization 头的值，格式：{sn} {sign}
    """
    sign = md5_sign(body_str, key)
    return f"{sn} {sign}"


def serialize_body(body: dict[str, Any]) -> str:
    """
    将请求体字典序列化为 JSON 字符串

    ⚠️ 关键：序列化后的字符串将同时用于签名和 HTTP 请求体，
    两者必须完全一致。不要分别序列化。

    Args:
        body: 请求参数字典

    Returns:
        JSON 字符串（UTF-8 编码，不转义非 ASCII 字符）
    """
    return json.dumps(body, ensure_ascii=False)


def build_signed_headers(sn: str, body_str: str, key: str) -> dict[str, str]:
    """
    构建带签名的完整 HTTP 请求头

    Args:
        sn: 序列号
        body_str: 请求体 JSON 字符串
        key: 密钥

    Returns:
        包含 Authorization 和 Content-Type 的请求头字典
    """
    return {
        "Authorization": build_authorization(sn, body_str, key),
        "Content-Type": "application/json; charset=utf-8",
    }
