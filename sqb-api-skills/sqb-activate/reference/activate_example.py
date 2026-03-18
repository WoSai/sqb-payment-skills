"""
收钱吧终端激活示例 (Python)

使用 vendor_sn + vendor_key 签名（与交易接口不同）
激活成功后获取 terminal_sn 和 terminal_key，用于后续交易签名
"""

import hashlib
import json
import requests

API_BASE = "https://vsi-api.shouqianba.com"

# 服务商凭证（替换为真实值）
VENDOR_SN = "your_vendor_sn"
VENDOR_KEY = "your_vendor_key"


def md5_sign(body_str: str, key: str) -> str:
    """计算 MD5 签名"""
    content = body_str + key
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def activate(app_id: str, code: str, device_id: str) -> dict | None:
    """
    终端激活

    Args:
        app_id: 应用ID
        code: 激活码（一次性使用）
        device_id: 设备唯一标识

    Returns:
        成功返回 {"terminal_sn": ..., "terminal_key": ...}，失败返回 None
    """
    # 1. 构建请求体
    body = {
        "app_id": app_id,
        "code": code,
        "device_id": device_id,
    }
    body_str = json.dumps(body, ensure_ascii=False)

    # 2. 计算签名（vendor 级别）
    sign = md5_sign(body_str, VENDOR_KEY)

    # 3. 发送请求
    headers = {
        "Authorization": f"{VENDOR_SN} {sign}",
        "Content-Type": "application/json; charset=utf-8",
    }

    resp = requests.post(
        f"{API_BASE}/terminal/activate",
        data=body_str.encode("utf-8"),
        headers=headers,
    )
    result = resp.json()

    # 4. 解析响应
    if result.get("result_code") != "200":
        print(f"通信失败: {result.get('error_code')} - {result.get('error_message')}")
        return None

    biz_response = result.get("biz_response", {})
    if biz_response.get("result_code") != "ACTIVATE_SUCCESS":
        print(f"激活失败: {biz_response.get('result_code')} - {biz_response.get('error_message')}")
        return None

    # 5. 提取凭证
    data = biz_response["data"]
    return {
        "terminal_sn": data["terminal_sn"],
        "terminal_key": data["terminal_key"],
    }


if __name__ == "__main__":
    result = activate(
        app_id="2019032019283301102",
        code="11000200",       # 激活码
        device_id="DEVICE_001",
    )

    if result:
        print("激活成功！")
        print(f"terminal_sn: {result['terminal_sn']}")
        print(f"terminal_key: {result['terminal_key']}")
        # TODO: 将 terminal_sn 和 terminal_key 持久化存储到数据库或配置文件
    else:
        print("激活失败，请检查激活码和服务商凭证")
