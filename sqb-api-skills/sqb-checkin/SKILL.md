---
name: sqb-checkin
description: "[后端项目使用]收钱吧终端签到接口技能。用于生成签到、terminal_key 刷新与容灾逻辑的分层适配代码。"
version: "2.0"
tags: [payment, terminal, checkin, key-rotation, adapter]
globs: ["**/*.java", "**/*.py"]
---

# 收钱吧终端签到接口

## 分层定位

完整流程生成时，本 skill 应输出：

- `protocol/dto`：签到请求与响应 DTO
- `adapter/terminal`：`SqbTerminalCheckinAdapter`
- `support/key_rotation`：密钥轮换与双 key 容灾
- `bootstrap`：定时签到或首次交易前签到骨架

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

- 签到请求构建
- checkin request
- 密钥轮换逻辑
- key rotation
- 双key容灾
- 签到容灾机制

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/terminal/checkin` |
| 请求方法 | POST |
| 签名 | `Authorization: {terminal_sn} {MD5(request_body + terminal_key)}` |

## 核心参数

- `terminal_sn`
- `terminal_key`
- `device_id`

## 完整流程生成

当用户要求完整接入时，生成内容至少包括：

1. `CheckinRequest` / `CheckinResponse`
2. `SqbTerminalCheckinAdapter.checkin(...)`
3. `SqbKeyRotationSupport`
4. 旧 key 备份与新 key 持久化逻辑
5. 分布式锁或单节点签到占位说明

## 单独模块生成

### 模块：签到请求构建

只生成签到请求 DTO 与请求发送逻辑。

### 模块：密钥轮换逻辑

只生成新旧 key 更新、持久化、失败处理流程。

### 模块：双 key 容灾

只生成超时重试、`ILLEGAL_SIGN` 判断、人工介入提示逻辑。

## 生成规则

1. 必须引用共享签名模块
2. 必须生成 `terminal_key` 更新逻辑
3. 必须包含完整密钥轮换容灾流程
4. 必须说明集群场景要做 key 同步
5. 必须保留重新激活提示
