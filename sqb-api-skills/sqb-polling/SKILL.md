---
name: sqb-polling
description: "收钱吧轮询框架模块。用于生成 support/polling 层中的参数化轮询策略、轮询执行器和超时结果模型。"
version: "2.0"
tags: [polling, retry, async, support, query]
globs: ["**/*.java", "**/*.py"]
---

# 收钱吧轮询框架

## 分层定位

本 skill 属于 `support/polling` 层。

它负责生成：

- 轮询配置 `PollingConfig`
- 轮询执行器 `pollUntilFinal(...)`
- 轮询结果模型 `PollingResult`

## 引导词

### 完整流程

- 轮询框架
- polling
- 轮询机制
- 自动查询
- 轮询策略
- poll until final
- 轮询逻辑
- 轮询间隔
- 支付轮询配置

### 单独模块

- polling runner
- polling policy
- query retry support

## 轮询策略

### PAY_POLLING_CONFIG

- phase1: 0~60s，每 3s
- phase2: 60s+，每 10s
- maxTimeout: 120s

### PRECREATE_POLLING_CONFIG

- phase1: 0~30s，每 2s
- phase2: 30s+，每 5s
- maxTimeout: 240s

## 目标输出

### 完整流程生成

在完整流程里，本 skill 应生成或被引用为：

- `support/polling/PollingConfig`
- `support/polling/PollingRunner`
- `support/polling/PollingResult`

### 单独模块生成

只生成轮询配置与执行逻辑，不生成 query adapter。

## 生成规则

1. 必须包含 `PollingConfig`
2. 必须包含 `PAY_POLLING_CONFIG`
3. 必须包含 `PRECREATE_POLLING_CONFIG`
4. 必须包含 `pollUntilFinal(queryFn, config, callback)`
5. 超时后返回 `TIMEOUT`，不抛异常
6. 查询异常时不中断轮询，可继续重试
7. 必须包含 `PollingResult`

## 代码示例

见 `reference/` 目录：

- `SqbPollingUtil.java`
- `sqb_polling_util.py`
