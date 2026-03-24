"""
收钱吧回调 RSA 验签工具

⚠️ 重要：验签是防止资金损失的最后一道防线，不可省略。

验签算法：RSA SHA256WithRSA（非对称签名，非 MD5）
Authorization 头格式（回调场景）：{terminal_sn} {base64_encoded_signature}

验签流程：
1. 从 Authorization header 提取 terminal_sn 和 Base64 编码的签名
2. 使用收钱吧 RSA 公钥 + SHA256WithRSA 算法验证
3. 验证对象是 HTTP body 的原始字节流
4. 验证失败立即返回 403

依赖安装：pip install cryptography
"""

import base64
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


# 公钥缓存
_sqb_public_key = None


def load_sqb_public_key():
    """
    加载收钱吧 RSA 公钥

    公钥来源：从收钱吧服务商平台获取。
    建议使用配置文件或密钥管理服务（KMS / Vault）安全存储。
    """
    global _sqb_public_key
    if _sqb_public_key is not None:
        return _sqb_public_key

    pem_path = os.environ.get("SQB_PUBLIC_KEY_PATH", "sqb_public_key.pem")
    with open(pem_path, "rb") as f:
        _sqb_public_key = serialization.load_pem_public_key(f.read())
    return _sqb_public_key


def verify_signature_rsa(body_bytes: bytes, auth_header: str) -> bool:
    """
    RSA SHA256WithRSA 回调验签

    Args:
        body_bytes: 原始请求体字节流
        auth_header: Authorization 请求头值，格式：{terminal_sn} {base64_signature}

    Returns:
        True=验签通过, False=验签失败
    """
    if not auth_header or " " not in auth_header:
        return False

    terminal_sn, received_sign_b64 = auth_header.split(" ", 1)

    try:
        signature_bytes = base64.b64decode(received_sign_b64)
        public_key = load_sqb_public_key()
        public_key.verify(
            signature_bytes,
            body_bytes,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception as e:
        print(f"RSA 验签失败 [terminal_sn={terminal_sn}]: {e}")
        return False
