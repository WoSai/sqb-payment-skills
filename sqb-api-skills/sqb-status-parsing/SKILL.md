---
name: sqb-status-parsing
description: "收钱吧三层状态判定模块。用于生成 support/status 层中的响应解析、最终状态判断与结构化结果输出。"
version: "2.0"
tags: [status, parsing, response, support, mapping]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧三层状态判定

## 分层定位

本 skill 属于 `support/status` 层。

它负责生成：

- 三层状态解析器
- 最终状态常量
- 结构化判定结果
- provider 状态到本地语义的映射辅助

## 引导词

### 完整流程

- 三层状态判定
- 状态解析
- status parsing
- order_status 判定
- 响应解析
- 交易结果判定
- result_code 解析
- 最终状态判断
- 非最终状态

### 单独模块

- status mapper
- 最终状态集合
- 结构化响应解析

## 三层判定模型

### 第一层：result_code

- `200`：通信成功
- 非 `200`：通信失败

### 第二层：biz_response.result_code

- 成功：`PAY_SUCCESS`、`PRECREATE_SUCCESS`、`REFUND_SUCCESS`、`CANCEL_SUCCESS`
- 确定失败：`PAY_FAIL`、`PRECREATE_FAIL`、`REFUND_FAIL`、`CANCEL_ABORT_ERROR`、`FAIL`
- 不确定：`PAY_FAIL_ERROR`、`PAY_IN_PROGRESS`、`REFUND_IN_PROGRESS`、`REFUND_FAIL_ERROR`、`CANCEL_ERROR`

### 第三层：order_status

- 最终状态：`PAID`、`PAY_CANCELED`、`REFUNDED`、`PARTIAL_REFUNDED`、`CANCELED`
- 非最终状态：`CREATED`、`PAY_ERROR`、`REFUND_ERROR`、`CANCEL_ERROR`

## 目标输出

### 完整流程生成

在完整流程里，本 skill 应为 `support/status` 层提供：

- `FINAL_ORDER_STATUSES`
- `BIZ_DEFINITE_FAIL_CODES`
- `BIZ_UNCERTAIN_CODES`
- `parseResponse(response)`

### 单独模块生成

只生成状态解析模块本身，不生成 HTTP 调用与控制器骨架。

## 生成规则

1. 必须包含 `FINAL_ORDER_STATUSES`
2. 必须包含 `BIZ_DEFINITE_FAIL_CODES`
3. 必须包含 `BIZ_UNCERTAIN_CODES`
4. 必须提供 `isFinalStatus(orderStatus)`
5. 必须提供 `parseResponse(response)`，返回结构化结果
6. 非最终状态必须显式标记为“需要轮询”

## 代码示例

见 `reference/` 目录：

- `SqbStatusUtil.java`
- `sqb_status_util.py`
