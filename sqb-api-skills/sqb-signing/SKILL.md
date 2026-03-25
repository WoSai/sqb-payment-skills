---
name: sqb-signing
description: "收钱吧 MD5 请求签名模块。用于生成 protocol/security 层中的请求签名、Authorization 头构建和请求体序列化能力。"
version: "2.0"
tags: [signing, md5, authorization, protocol, security]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧 MD5 请求签名

## 分层定位

本 skill 属于 `protocol/security` 层。

它负责生成：

- `md5Sign(bodyStr, key)`
- `buildAuthorization(sn, bodyStr, key)`
- `serializeBody(body)`
- 可复用的签名辅助类 / 模块

它不负责生成：

- 具体支付、退款、查询业务流程
- 订单状态判定
- 轮询逻辑

## 引导词

### 完整流程

- 收钱吧签名
- MD5 签名
- 请求签名
- Authorization 头
- signing
- 签名工具
- sign util
- 签名逻辑
- 收钱吧 Authorization

### 单独模块

- request signer
- protocol security
- Authorization 构建

## 概述

收钱吧所有请求接口统一使用 MD5 签名机制：

```text
sign = MD5(request_body + key)
Authorization = {sn} {sign}
```

## 两种凭证

| 场景 | sn | key | 说明 |
|---|---|---|---|
| 激活接口 | `vendor_sn` | `vendor_key` | 仅 `/terminal/activate` 使用 |
| 其他接口 | `terminal_sn` | `terminal_key` | 支付、查询、退款、撤单、签到等 |

## 关键约束

1. `request_body` 必须是 UTF-8 编码的原始 JSON 字符串
2. 签名时使用的字符串必须和实际 HTTP 请求体完全一致
3. MD5 输出必须是 32 位小写十六进制
4. Authorization 头格式必须为 `{sn} {sign}`，中间有且仅有一个空格
5. `Content-Type` 必须为 `application/json; charset=utf-8`

## 目标输出

### 完整流程生成

当 AI 在完整流程中引用本 skill 时，应在 `protocol/security` 层生成：

- `SqbRequestSigner`
- `SqbAuthorizationBuilder`
- 请求体序列化约束说明

### 单独模块生成

当用户只需要签名模块时，只生成：

- 一个独立可复用的签名类 / 模块
- 必要的序列化辅助函数
- 调用示例

## 生成规则

1. 必须包含 `md5Sign(bodyStr, key)` 函数
2. 必须包含 `buildAuthorization(sn, bodyStr, key)` 函数
3. 必须包含 `serializeBody(body)` 函数
4. 必须注释说明：**序列化后的 body 字符串同时用于签名与请求发送**
5. 必须注释区分 vendor 签名和 terminal 签名
6. 不得在各接口 skill 内重新发明一套签名实现

## 代码示例

见 `reference/` 目录：

- `SqbSignUtil.java`
- `sqb_sign_util.py`
