"""
收钱吧终端签到示例 (Python)

签到会更新 terminal_key，必须持久化新 key
建议每日首次交易前签到
"""

import hashlib
import json
import requests

API_BASE = "https://vsi-api.shouqianba.com"


def md5_sign(body_str: str, key: str) -> str:
    """计算 MD5 签名"""
    content = body_str + key
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def checkin(terminal_sn: str, terminal_key: str, device_id: str) -> str | None:
    """
    终端签到

    Args:
        terminal_sn: 终端序列号
        terminal_key: 当前终端密钥
        device_id: 设备唯一标识

    Returns:
        成功返回新的 terminal_key，失败返回 None
    """
    # 1. 构建请求体
    body = {
        "terminal_sn": terminal_sn,
        "device_id": device_id,
    }
    body_str = json.dumps(body, ensure_ascii=False)

    # 2. 计算签名（terminal 级别）
    sign = md5_sign(body_str, terminal_key)

    # 3. 发送请求
    headers = {
        "Authorization": f"{terminal_sn} {sign}",
        "Content-Type": "application/json; charset=utf-8",
    }

    resp = requests.post(
        f"{API_BASE}/terminal/checkin",
        data=body_str.encode("utf-8"),
        headers=headers,
    )
    result = resp.json()

    # 4. 解析响应
    if result.get("result_code") != "200":
        print(f"签到通信失败: {result.get('error_code')} - {result.get('error_message')}")
        return None

    biz_response = result.get("biz_response", {})
    if biz_response.get("result_code") != "TERMINAL_CHECKIN_SUCCESS":
        print(f"签到失败: {biz_response.get('result_code')}")
        print("如持续失败，请重新激活终端")
        return None

    # 5. 获取新 key（关键！）
    new_key = biz_response["data"]["terminal_key"]
    print(f"签到成功，新 terminal_key: {new_key}")
    return new_key


def checkin_and_update(terminal_sn: str, terminal_key: str, device_id: str) -> str:
    """签到并更新存储"""
    new_key = checkin(terminal_sn, terminal_key, device_id)
    if new_key:
        # TODO: 更新持久化存储中的 terminal_key
        # db.execute("UPDATE terminal SET terminal_key = %s WHERE terminal_sn = %s", new_key, terminal_sn)
        print("terminal_key 已更新，请确保持久化存储已同步")
        return new_key
    else:
        print("签到失败，保留旧 key")
        return terminal_key


if __name__ == "__main__":
    # 替换为真实值
    TERMINAL_SN = "your_terminal_sn"
    TERMINAL_KEY = "your_terminal_key"
    DEVICE_ID = "DEVICE_001"

    new_key = checkin_and_update(TERMINAL_SN, TERMINAL_KEY, DEVICE_ID)
