---
name: sqb-status-parsing
description: "收钱吧三层状态判定工具。当用户需要单独生成响应解析逻辑、状态判定、三层判定时触发。"
version: "1.0"
tags: [status, parsing, response, three-layer, utility]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧三层状态判定

## 引导词

- 三层状态判定
- 状态解析
- status parsing
- order_status 判定
- 响应解析
- 交易结果判定
- result_code 解析
- 最终状态判断
- 非最终状态

## 概述

收钱吧 API 响应采用三层状态判定模型，必须逐层解析才能正确判断交易结果。仅检查第一层 `result_code` 是不够的——必须深入到第三层 `order_status` 才能确定交易最终结果。

## 三层判定模型

### 第一层：result_code（通信层）

| result_code | 含义 | 处理 |
|---|---|---|
| `200` | 通信成功 | 继续判断 biz_response |
| 非 `200` | 通信失败 | 根据 error_code 处理，可能需要重试 |

### 第二层：biz_response.result_code（业务层）

| 分类 | result_code 值 | 处理 |
|---|---|---|
| 成功 | PAY_SUCCESS, PRECREATE_SUCCESS, REFUND_SUCCESS, CANCEL_SUCCESS | 检查 order_status |
| 确定失败 | PAY_FAIL, PRECREATE_FAIL, REFUND_FAIL, CANCEL_ABORT_ERROR, FAIL | 交易结束，无需轮询 |
| 不确定 | PAY_FAIL_ERROR, PAY_IN_PROGRESS, REFUND_IN_PROGRESS, CANCEL_ERROR | **必须轮询查询** |

### 第三层：order_status（订单最终状态）

| order_status | 类型 | 含义 |
|---|---|---|
| `PAID` | **最终状态** | 支付成功 |
| `PAY_CANCELED` | **最终状态** | 支付已撤销 |
| `REFUNDED` | **最终状态** | 全额退款成功 |
| `PARTIAL_REFUNDED` | **最终状态** | 部分退款成功 |
| `CANCELED` | **最终状态** | 订单已撤销 |
| `CREATED` | 非最终状态 | 订单已创建，**必须轮询** |
| `PAY_ERROR` | 非最终状态 | 状态未知，**必须轮询** |
| `REFUND_ERROR` | 非最终状态 | 退款状态未知，**必须轮询** |
| `CANCEL_ERROR` | 非最终状态 | 撤单状态未知，**必须轮询** |

> **重要**：收到非最终状态时，**禁止**直接判定为成功或失败，必须启动轮询查询。

## 生成规则

当用户需要单独生成状态判定模块时，**必须**包含：

1. 最终状态集合常量 `FINAL_ORDER_STATUSES`（PAID, PAY_CANCELED, REFUNDED, PARTIAL_REFUNDED, CANCELED）
2. 确定失败码集合常量 `BIZ_DEFINITE_FAIL_CODES`（PAY_FAIL, PRECREATE_FAIL, REFUND_FAIL, CANCEL_ABORT_ERROR, FAIL）
3. 不确定码集合常量 `BIZ_UNCERTAIN_CODES`（PAY_FAIL_ERROR, PAY_IN_PROGRESS, REFUND_IN_PROGRESS, REFUND_FAIL_ERROR, CANCEL_ERROR）
4. `isFinalStatus(orderStatus)` 函数：判断是否为最终状态
5. `parseResponse(response)` 函数：实现三层判定，返回结构化结果（status/orderStatus/sn/clientSn/message/isFinal）
6. 非最终状态的返回结果中 isFinal=false，标记为"需要轮询"

## 代码示例

见 `reference/` 目录：
- `SqbStatusUtil.java` — Java 三层状态判定工具
- `sqb_status_util.py` — Python 三层状态判定工具
