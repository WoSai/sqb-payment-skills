"""
收钱吧终端签到示例 (Python)

签到会更新 terminal_key，必须持久化新 key。
建议每日首次交易前签到。

⚠️ 警告：签到涉及密钥轮换，实现不当可能导致终端无法交易。
必须完整实现容灾逻辑（备份旧 key → 签到 → 更新新 key → 失败重试 → 告警）。
"""

import hashlib
import json
import logging
import time

import requests

API_BASE = "https://vsi-api.shouqianba.com"
logger = logging.getLogger(__name__)


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
    body = {
        "terminal_sn": terminal_sn,
        "device_id": device_id,
    }
    body_str = json.dumps(body, ensure_ascii=False)
    sign = md5_sign(body_str, terminal_key)

    headers = {
        "Authorization": f"{terminal_sn} {sign}",
        "Content-Type": "application/json; charset=utf-8",
    }

    resp = requests.post(
        f"{API_BASE}/terminal/checkin",
        data=body_str.encode("utf-8"),
        headers=headers,
        timeout=15,
    )
    result = resp.json()

    if result.get("result_code") != "200":
        error_code = result.get("error_code", "UNKNOWN")
        error_msg = result.get("error_message", "")
        logger.error(f"签到通信失败: [{error_code}] {error_msg}")
        return None

    biz_response = result.get("biz_response", {})
    if biz_response.get("result_code") != "TERMINAL_CHECKIN_SUCCESS":
        logger.error(f"签到失败: {biz_response.get('result_code')}")
        return None

    new_key = biz_response["data"]["terminal_key"]
    logger.info(f"签到成功，terminal_key 已更新")
    return new_key


def checkin_with_disaster_recovery(
    terminal_sn: str,
    terminal_key: str,
    device_id: str,
    save_key_fn=None,
    alert_fn=None,
) -> str:
    """
    带容灾逻辑的签到流程

    容灾步骤：
    1. 签到前：备份旧 key
    2. 签到成功：持久化新 key
    3. 网络异常：用旧 key 重试
    4. 两次重试都失败：记录告警，标记需人工介入

    Args:
        terminal_sn: 终端序列号
        terminal_key: 当前终端密钥
        device_id: 设备唯一标识
        save_key_fn: 持久化 key 的回调函数 fn(terminal_sn, new_key, old_key)
        alert_fn: 告警回调函数 fn(terminal_sn, error_message)

    Returns:
        当前有效的 terminal_key（成功返回新 key，失败返回旧 key）
    """
    # ── Step 1: 备份旧 key ──
    old_key = terminal_key
    logger.info(f"签到开始 [terminal_sn={terminal_sn}]，已备份旧 key")

    # ── Step 2: 首次签到尝试 ──
    try:
        new_key = checkin(terminal_sn, terminal_key, device_id)
        if new_key:
            # 签到成功，持久化新 key
            if save_key_fn:
                save_key_fn(terminal_sn, new_key, old_key)
            logger.info(f"签到成功，密钥已更新 [terminal_sn={terminal_sn}]")
            return new_key
    except requests.exceptions.RequestException as e:
        logger.warning(f"签到网络异常: {e}")

    # ── Step 3: 第一次重试（用旧 key） ──
    logger.info("签到失败，1 秒后用旧 key 重试...")
    time.sleep(1)

    try:
        new_key = checkin(terminal_sn, old_key, device_id)
        if new_key:
            if save_key_fn:
                save_key_fn(terminal_sn, new_key, old_key)
            logger.info(f"重试签到成功 [terminal_sn={terminal_sn}]")
            return new_key
    except requests.exceptions.RequestException as e:
        logger.warning(f"第一次重试网络异常: {e}")

    # ── Step 4: 第二次重试 ──
    logger.info("第一次重试失败，2 秒后第二次重试...")
    time.sleep(2)

    try:
        new_key = checkin(terminal_sn, old_key, device_id)
        if new_key:
            if save_key_fn:
                save_key_fn(terminal_sn, new_key, old_key)
            logger.info(f"第二次重试签到成功 [terminal_sn={terminal_sn}]")
            return new_key
    except requests.exceptions.RequestException as e:
        logger.error(f"第二次重试网络异常: {e}")

    # ── Step 5: 两次重试都失败，触发告警 ──
    error_msg = (
        f"终端签到连续失败 [terminal_sn={terminal_sn}]。"
        f"密钥状态可能不一致，需人工介入。"
        f"可能需要重新激活终端（联系运营获取新激活码）。"
    )
    logger.critical(error_msg)

    if alert_fn:
        alert_fn(terminal_sn, error_msg)

    # 返回旧 key（可能已失效，但这是目前唯一已知的 key）
    return old_key


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 替换为真实值
    TERMINAL_SN = "your_terminal_sn"
    TERMINAL_KEY = "your_terminal_key"
    DEVICE_ID = "DEVICE_001"

    def save_key(sn, new_key, old_key):
        """持久化密钥（替换为真实的数据库/配置更新逻辑）"""
        # db.execute("UPDATE terminal SET terminal_key=%s, old_terminal_key=%s WHERE terminal_sn=%s",
        #            new_key, old_key, sn)
        print(f"密钥已持久化: terminal_sn={sn}")

    def alert(sn, msg):
        """告警通知（替换为真实的告警逻辑：钉钉/企微/邮件等）"""
        print(f"⚠️ 告警: {msg}")

    new_key = checkin_with_disaster_recovery(
        TERMINAL_SN, TERMINAL_KEY, DEVICE_ID,
        save_key_fn=save_key,
        alert_fn=alert,
    )
