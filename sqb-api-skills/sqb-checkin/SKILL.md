---
name: sqb-checkin
description: "[后端项目使用]收钱吧终端签到接口技能。用于保持终端活跃并更新terminal_key。当用户提到收钱吧签到、终端签到、terminal checkin、刷新密钥时触发。"
version: "1.1"
tags: [payment, terminal, checkin, key-rotation]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧终端签到接口

## 引导词

### 完整流程
- 收钱吧签到
- 终端签到
- terminal checkin
- 刷新密钥
- key 更新
- sqb-checkin
- terminal check-in
- /terminal/checkin
- 密钥刷新
- 密钥轮换

### 单独模块
- 签到请求构建 / checkin request（→ 仅生成签到请求模块）
- 密钥轮换逻辑 / key rotation（→ 仅生成密钥轮换模块）
- 双key容灾 / 签到容灾机制（→ 仅生成容灾机制模块）

## 概述

终端签到用于保持终端活跃状态并更新 `terminal_key`。建议每天至少签到一次，通常在每日首次交易前执行。

## 前置条件

- 已完成终端激活（sqb-activate），持有 `terminal_sn` 和 `terminal_key`
- API 域名：`https://vsi-api.shouqianba.com`

## 接口信息

- **URL**: `/terminal/checkin`
- **方法**: POST
- **Content-Type**: `application/json; charset=utf-8`

## 签名方式

```
Authorization: {terminal_sn} {MD5(request_body + terminal_key)}
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| terminal_sn | string | Y | 终端序列号 |
| device_id | string | Y | 设备唯一标识 |
| os_info | string | N | 操作系统信息 |
| sdk_version | string | N | SDK 版本 |

## 请求示例

```json
{
    "terminal_sn": "10298371039",
    "device_id": "DEVICE_001"
}
```

## 响应参数

| 参数 | 说明 |
|---|---|
| terminal_sn | 终端序列号 |
| terminal_key | **新的**终端密钥，必须更新本地存储 |

## 响应示例

```json
{
    "result_code": "200",
    "biz_response": {
        "result_code": "TERMINAL_CHECKIN_SUCCESS",
        "data": {
            "terminal_sn": "10298371039",
            "terminal_key": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
        }
    }
}
```

## 陷阱与注意事项

### 1. 密钥轮换（最大风险点）

每次签到成功后，`terminal_key` 会更新为新值。**必须立即用新 key 替换旧 key**。

```
签到前：terminal_key = "old_key_xxx"
签到后：terminal_key = "new_key_yyy"  ← 必须持久化保存
```

### 2. 签到失败时的密钥状态不确定

如果签到请求已发送但未收到响应（网络超时等），密钥可能已在服务端更新，此时：
- 本地旧 key 可能已失效
- 新 key 未知

**解决方案**：
1. 先用旧 key 重试签到
2. 如果旧 key 签名失败（返回签名错误），说明 key 已在服务端更新
3. 此时只能**重新激活终端**（需新激活码）

### 3. 集群部署同步

在分布式部署环境中：
- 签到操作应由单一节点执行
- 新 key 获取后必须同步到所有节点
- 建议使用分布式锁防止多节点同时签到

### 4. 密钥有效期

- `terminal_key` 每日自然日过期
- 签到后，当前 key 和上一个 key 同时有效（双 key 机制）
- 无效/过期的 key 会触发 `ILLEGAL_SIGN` 错误

### 5. 签到频率

- 建议每日首次交易前签到
- 不要过于频繁签到（避免密钥频繁更新带来的同步风险）
- 长期不签到可能导致终端被标记为不活跃

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/terminal/checkin` |
| 请求方法 | POST |
| Content-Type | `application/json; charset=utf-8` |
| API 域名 | `https://vsi-api.shouqianba.com` |

## 密钥轮换容灾逻辑（必须编码为代码模板）

签到涉及密钥更新，网络异常时可能导致本地和服务端密钥不一致。**以下容灾流程必须完整实现**：

```
1. 签到前：将当前 terminal_key 持久化到 old_terminal_key 字段（备份）
2. 发起签到请求
3. 收到成功响应（TERMINAL_CHECKIN_SUCCESS）：
   a. 将新 terminal_key 写入持久化存储
   b. 保留 old_terminal_key 作为备份（双 key 机制期间可用）
4. 网络异常 / 超时（未收到响应）：
   a. 用旧 key 重试签到（第一次重试）
   b. 如果收到 ILLEGAL_SIGN 错误：说明服务端已更新 key，旧 key 失效
   c. 用旧 key 再重试一次（第二次重试，利用双 key 机制窗口）
5. 两次重试都失败：
   a. 记录告警日志（包含 terminal_sn、失败原因、时间戳）
   b. 标记终端为"需人工介入"状态
   c. 提示：可能需要重新激活终端（联系运营获取新激活码）
6. 集群部署额外步骤：
   a. 使用分布式锁确保单节点执行签到
   b. 签到成功后同步新 key 到所有节点
   c. 所有节点确认收到新 key 后才释放锁
```

## 生成规则

当生成签到接口代码时，**必须**包含：
1. 签名逻辑引用 `shared-reference/SqbSignUtil`
2. **签到成功后更新 terminal_key 的逻辑**（核心）
3. **完整的密钥轮换容灾逻辑**（签到前备份、失败重试、告警）
4. 密钥持久化更新逻辑
5. 签到失败的异常处理（含重新激活提示）
6. 建议包含定时签到的调度逻辑

## 模块化生成

本技能支持单独生成以下模块。当用户 prompt 中包含模块关键词时，仅生成对应模块代码，不生成完整流程。无模块关键词时，按上方"生成规则"生成完整代码。

> 签名等跨接口共享模块请使用对应的独立 Skill（sqb-signing）。

### 模块：签到请求构建

**触发关键词**："签到请求构建"、"checkin request"、"构建签到报文"

**生成规则**：
1. 构建 JSON 请求体，包含 terminal_sn、device_id（必填）
2. 使用 terminal 级别签名
3. POST 请求到 `/terminal/checkin`

**参考代码（Java）**：
```java
// 签到请求构建
ObjectNode body = mapper.createObjectNode();
body.put("terminal_sn", terminalSn);
body.put("device_id", deviceId);

String bodyStr = mapper.writeValueAsString(body);
String sign = SqbSignUtil.md5Sign(bodyStr, terminalKey);

Request request = new Request.Builder()
    .url("https://vsi-api.shouqianba.com/terminal/checkin")
    .addHeader("Authorization", terminalSn + " " + sign)
    .addHeader("Content-Type", "application/json; charset=utf-8")
    .post(RequestBody.create(bodyStr, JSON_TYPE))
    .build();
```

**参考代码（Python）**：
```python
# 签到请求构建
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
    "https://vsi-api.shouqianba.com/terminal/checkin",
    data=body_str.encode("utf-8"),
    headers=headers,
    timeout=30,
)
```

### 模块：密钥轮换逻辑

**触发关键词**："密钥轮换"、"key rotation"、"terminal_key更新"

**生成规则**：
1. 签到成功后，立即用新 terminal_key 替换旧 terminal_key
2. 持久化新 key 到存储
3. 集群部署时同步到所有节点

**参考代码（Java）**：
```java
// 密钥轮换：签到成功后更新 terminal_key
String newTerminalKey = data.get("terminal_key").asText();
terminalKeyStore.save(terminalSn, newTerminalKey);
log.info("签到成功，terminal_key 已更新: terminal_sn={}", terminalSn);
// 集群部署时，需将新 key 同步到所有节点
```

**参考代码（Python）**：
```python
# 密钥轮换：签到成功后更新 terminal_key
new_terminal_key = data["terminal_key"]
save_terminal_key(terminal_sn, new_terminal_key)
logger.info(f"签到成功，terminal_key 已更新: terminal_sn={terminal_sn}")
# 集群部署时，需将新 key 同步到所有节点
```

### 模块：双 key 容灾机制

**触发关键词**："双key容灾"、"签到容灾"、"ILLEGAL_SIGN处理"、"签到失败恢复"

**生成规则**：
1. 签到前备份当前 terminal_key 到 old_terminal_key
2. 网络异常时，用旧 key 重试签到
3. 收到 ILLEGAL_SIGN 错误时，说明服务端已更新 key
4. 两次重试均失败时，标记需人工介入（重新激活）
5. 利用收钱吧双 key 机制的容错窗口

**参考代码（Java）**：
```java
// 双 key 容灾机制
String oldKey = terminalKeyStore.get(terminalSn);
terminalKeyStore.saveBackup(terminalSn, oldKey);  // 备份旧 key

try {
    CheckinResponse resp = doCheckin(terminalSn, oldKey);
    terminalKeyStore.save(terminalSn, resp.getNewKey());  // 更新新 key
} catch (TimeoutException e) {
    // 第一次重试：用旧 key
    try {
        CheckinResponse resp = doCheckin(terminalSn, oldKey);
        terminalKeyStore.save(terminalSn, resp.getNewKey());
    } catch (IllegalSignException ex) {
        // 旧 key 已失效，服务端已更新 → 需重新激活
        log.error("签到容灾失败，需重新激活终端: terminal_sn={}", terminalSn);
        markTerminalNeedsReactivation(terminalSn);
    }
}
```

**参考代码（Python）**：
```python
# 双 key 容灾机制
old_key = get_terminal_key(terminal_sn)
save_backup_key(terminal_sn, old_key)  # 备份旧 key

try:
    resp = do_checkin(terminal_sn, old_key)
    save_terminal_key(terminal_sn, resp["terminal_key"])  # 更新新 key
except TimeoutError:
    # 第一次重试：用旧 key
    try:
        resp = do_checkin(terminal_sn, old_key)
        save_terminal_key(terminal_sn, resp["terminal_key"])
    except IllegalSignError:
        # 旧 key 已失效，服务端已更新 → 需重新激活
        logger.error(f"签到容灾失败，需重新激活终端: terminal_sn={terminal_sn}")
        mark_terminal_needs_reactivation(terminal_sn)
```

## 代码示例

见 `reference/` 目录：
- `CheckinExample.java` — Java 示例（OkHttp + Jackson）
- `checkin_example.py` — Python 示例（requests）
