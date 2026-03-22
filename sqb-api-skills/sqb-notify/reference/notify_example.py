"""
收钱吧异步回调通知处理示例 (Python Flask)

⚠️ 警告：收钱吧没有沙盒环境，此代码处理的是真实交易回调。
回调是对主动轮询的补充，不能完全替代主动查询。
必须做幂等处理和 RSA 签名验证——验签是防止资金损失的最后一道防线。

依赖安装：pip install flask cryptography
"""

import base64
import json
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from flask import Flask, request

app = Flask(__name__)


def load_sqb_public_key():
    """
    加载收钱吧 RSA 公钥

    公钥来源：从收钱吧服务商平台获取。
    建议使用配置文件或密钥管理服务（KMS / Vault）安全存储。
    """
    pem_path = os.environ.get("SQB_PUBLIC_KEY_PATH", "sqb_public_key.pem")
    with open(pem_path, "rb") as f:
        return serialization.load_pem_public_key(f.read())


# 启动时加载公钥（避免每次请求读文件）
SQB_PUBLIC_KEY = None


def get_public_key():
    global SQB_PUBLIC_KEY
    if SQB_PUBLIC_KEY is None:
        SQB_PUBLIC_KEY = load_sqb_public_key()
    return SQB_PUBLIC_KEY


def verify_signature_rsa(body_bytes: bytes, auth_header: str) -> bool:
    """
    RSA SHA256WithRSA 回调验签

    验签流程：
    1. 从 Authorization header 提取 terminal_sn 和 Base64 编码的签名
    2. 使用收钱吧 RSA 公钥 + SHA256WithRSA 算法验证签名
    3. 验签失败返回 False

    Args:
        body_bytes: 原始请求体字节流
        auth_header: Authorization 请求头值

    Returns:
        True=验签通过, False=验签失败
    """
    if not auth_header or " " not in auth_header:
        return False

    terminal_sn, received_sign_b64 = auth_header.split(" ", 1)

    try:
        signature_bytes = base64.b64decode(received_sign_b64)
        public_key = get_public_key()
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


@app.route("/api/shouqianba/notify", methods=["POST"])
def handle_notify():
    """
    接收收钱吧回调通知

    配置方式：在支付请求中设置 notify_url 参数
    例如：notify_url = "https://your-domain.com/api/shouqianba/notify"
    """
    # 1. 获取原始请求体和签名头
    body_bytes = request.get_data()
    auth_header = request.headers.get("Authorization", "")

    # 2. RSA 验签（安全关键，不可跳过）
    if not verify_signature_rsa(body_bytes, auth_header):
        print("⚠️ 回调签名验证失败，拒绝处理——可能是伪造请求")
        return "FAIL", 403

    # 3. 解析回调数据
    try:
        data = json.loads(body_bytes)
    except json.JSONDecodeError:
        print("回调数据 JSON 解析失败")
        return "FAIL", 400

    sn = data.get("sn")
    client_sn = data.get("client_sn")
    order_status = data.get("order_status")
    total_amount = data.get("total_amount")

    print(f"收到回调通知: sn={sn}, client_sn={client_sn}, status={order_status}")

    # 4. 幂等处理：检查订单是否已处理
    # order = order_service.get_by_client_sn(client_sn)
    # if order and order.is_final_status():
    #     return "success", 200  # 已处理，直接返回成功

    # 5. 根据状态更新订单
    if order_status == "PAID":
        # order_service.mark_as_paid(client_sn, sn, total_amount)
        print(f"订单支付成功: {client_sn}")

    elif order_status == "PAY_CANCELED":
        # order_service.mark_as_canceled(client_sn)
        print(f"订单支付取消: {client_sn}")

    elif order_status == "REFUNDED":
        # order_service.mark_as_refunded(client_sn)
        print(f"订单已全额退款: {client_sn}")

    elif order_status == "PARTIAL_REFUNDED":
        refunded_amount = data.get("refunded_amount")
        # order_service.mark_as_partial_refunded(client_sn, refunded_amount)
        print(f"订单已部分退款: {client_sn}, 退款额: {refunded_amount}")

    else:
        print(f"收到非最终状态回调: {order_status}")

    # 6. 返回 success 文本表示接收成功
    return "success", 200


if __name__ == "__main__":
    # 注意：生产环境应使用 gunicorn 等 WSGI 服务器
    # 且必须配置 HTTPS
    app.run(host="0.0.0.0", port=8080)
