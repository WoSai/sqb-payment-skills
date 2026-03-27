---
name: sqb-notify
description: "[后端项目使用]收钱吧异步回调通知技能。用于生成回调接收、RSA 验签、幂等与状态分发的分层适配代码。"
version: "2.0"
tags: [payment, notify, webhook, callback, adapter]
globs: ["**/*.java", "**/*.py"]
---

# 收钱吧异步回调通知

## 分层定位

完整流程生成时，本 skill 应输出：

- `protocol/security`：RSA 验签模块引用
- `protocol/dto/notify`
- `adapter/terminal` 或 `adapter/notify`：回调处理器
- `support/idempotency`：回调幂等
- `bootstrap/controller`：HTTP POST 回调入口

## 引导词

### 完整流程

- 收钱吧回调
- 支付通知
- 异步通知
- notify
- webhook
- 回调处理
- callback handler
- 回调接口
- notify_url

### 单独模块

- 回调验签
- RSA验签
- callback verify
- 幂等处理
- 回调去重
- idempotent
- 回调分发
- 状态分发逻辑
- 公钥管理
- RSA公钥配置

## 回调机制

- 方法：POST
- `Content-Type: application/json`
- 回调可能重复
- 回调顺序不保证
- 未返回 `success` 时会重试

## 强制要求

### 验签不可省略

必须使用 `SHA256WithRSA` 对原始 `request_body` 验签。

### 幂等不可省略

必须使用 `sn` 或 `client_sn` 做幂等键，避免重复处理。

## 完整流程生成

至少生成以下内容：

1. 回调请求 DTO
2. 对 `sqb-callback-verify` 的引用
3. `SqbNotifyHandler` 或等价适配器
4. 幂等去重逻辑
5. `NotifyController` 或等价 HTTP 入口
6. 返回纯文本 `success`

## 单独模块生成

### 模块：RSA 回调验签

只生成验签模块，不生成控制器。

### 模块：幂等处理

只生成回调去重逻辑。

### 模块：回调分发

只生成状态分发与订单更新调用骨架。

### 模块：公钥管理

只生成公钥加载与缓存模块。

## 生成规则

1. 必须包含 RSA SHA256WithRSA 验签
2. 验签失败必须直接拒绝
3. 必须包含幂等处理
4. 必须返回 `success`
5. 必须记录异常与日志
