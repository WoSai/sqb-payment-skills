---
name: sqb-query
description: "[后端项目使用]收钱吧订单查询接口技能。用于生成查询适配器与轮询兜底能力。"
version: "2.0"
tags: [payment, query, polling, adapter]
globs: ["**/*.java", "**/*.py"]
---

# 收钱吧订单查询接口

## 分层定位

完整流程生成时，本 skill 应输出：

- `protocol/dto/query`
- `adapter/query`：`SqbQueryAdapter`
- `support/status`
- `support/polling`

## 引导词

### 完整流程

- 收钱吧查询
- 订单查询
- 交易查询
- query order
- /query
- 查询订单状态
- 轮询
- /upay/v2/query
- order status
- 支付结果查询

### 单独模块

- 查询请求构建
- query request
- 订单状态判定
- status判定
- 最终状态判定
- 轮询框架集成
- polling集成
- query adapter

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/upay/v2/query` |
| 请求方法 | POST |
| 核心参数 | `terminal_sn`, `sn`, `client_sn` |

## 状态范围

最终状态：

- `PAID`
- `PAY_CANCELED`
- `REFUNDED`
- `PARTIAL_REFUNDED`
- `CANCELED`

非最终状态：

- `CREATED`
- `PAY_ERROR`
- `REFUND_ERROR`
- `CANCEL_ERROR`

## 完整流程生成

至少生成以下内容：

1. `QueryRequest` / `QueryResponse`
2. `SqbQueryAdapter.query(...)`
3. `SqbStatusParser` 或共享状态模块引用
4. `PollingRunner` 集成示例
5. 超时处理机制
6. 无沙盒环境警告

## 单独模块生成

### 模块：查询请求构建

只生成请求构建与签名调用，支持 `sn` / `client_sn` 二选一。

### 模块：订单状态判定

只生成最终 / 非最终状态判断与结构化输出。

### 模块：轮询框架集成

只生成 query adapter 与 polling runner 的集成层。

## 生成规则

1. 必须支持 `sn` 和 `client_sn`
2. 必须引用共享签名模块
3. 必须引用状态判定模块
4. 轮询集成必须使用共享轮询模块
5. 必须保留无沙盒环境警告
