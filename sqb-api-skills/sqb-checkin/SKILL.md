---
name: sqb-checkin
description: 收钱吧终端签到接口。当用户提到"收钱吧签到"、"终端签到"、"terminal checkin"、"刷新密钥"时触发。
---

# 收钱吧终端签到接口

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

### 4. 签到频率

- 建议每日首次交易前签到
- 不要过于频繁签到（避免密钥频繁更新带来的同步风险）
- 长期不签到可能导致终端被标记为不活跃

## 生成规则

当生成签到接口代码时，必须包含：
1. terminal 级别签名逻辑
2. **签到成功后更新 terminal_key 的逻辑**（核心）
3. 密钥持久化更新逻辑
4. 签到失败的异常处理（含重新激活提示）
5. 建议包含定时签到的调度逻辑

## 参考代码

见 `reference/` 目录下的多语言示例。
