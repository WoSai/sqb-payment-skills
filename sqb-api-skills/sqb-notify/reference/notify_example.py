"""
收钱吧异步回调通知处理示例 (Python Flask)

回调是对主动轮询的补充，不能完全替代主动查询
必须做幂等处理和签名验证
"""

import hashlib
import json

from flask import Flask, request, jsonify

app = Flask(__name__)


def md5_sign(body_str: str, key: str) -> str:
    """计算 MD5 签名"""
    content = body_str + key
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def get_terminal_key(terminal_sn: str) -> str | None:
    """
    从存储中获取终端密钥
    TODO: 替换为真实的数据库查询逻辑
    """
    # return db.query("SELECT terminal_key FROM terminals WHERE terminal_sn = %s", terminal_sn)
    return "your_terminal_key"


def verify_signature(body: str, auth_header: str) -> bool:
    """验证回调签名"""
    if not auth_header or " " not in auth_header:
        return False

    terminal_sn, received_sign = auth_header.split(" ", 1)
    terminal_key = get_terminal_key(terminal_sn)

    if not terminal_key:
        print(f"未找到终端: {terminal_sn}")
        return False

    expected_sign = md5_sign(body, terminal_key)
    return expected_sign == received_sign


@app.route("/api/shouqianba/notify", methods=["POST"])
def handle_notify():
    """
    接收收钱吧回调通知

    配置方式：在支付请求中设置 notify_url 参数
    例如：notify_url = "https://your-domain.com/api/shouqianba/notify"
    """
    # 1. 获取原始请求体和签名头
    body = request.get_data(as_text=True)
    auth_header = request.headers.get("Authorization", "")

    # 2. 验证签名
    if not verify_signature(body, auth_header):
        print("回调签名验证失败，可能是伪造请求")
        return "FAIL", 400

    # 3. 解析回调数据
    data = json.loads(body)
    sn = data.get("sn")
    client_sn = data.get("client_sn")
    order_status = data.get("order_status")
    total_amount = data.get("total_amount")

    print(f"收到回调通知: sn={sn}, client_sn={client_sn}, status={order_status}")

    # 4. 幂等处理：检查订单是否已处理
    # order = order_service.get_by_client_sn(client_sn)
    # if order and order.is_final_status():
    #     return "200", 200  # 已处理，直接返回成功

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

    # 6. 返回 200 表示接收成功
    return "200", 200


if __name__ == "__main__":
    # 注意：生产环境应使用 gunicorn 等 WSGI 服务器
    # 且必须配置 HTTPS
    app.run(host="0.0.0.0", port=8080)
