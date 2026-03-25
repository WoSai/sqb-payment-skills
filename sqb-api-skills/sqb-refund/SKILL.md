---
name: sqb-refund
description: "[后端项目使用]收钱吧退款接口技能。用于生成全额退款与部分退款的分层适配代码。"
version: "2.0"
tags: [payment, refund, partial-refund, adapter]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧退款接口

## 分层定位

完整流程生成时，本 skill 应输出：

- `protocol/dto/refund`
- `adapter/refund`：`SqbRefundAdapter`
- `support/status`
- `support/polling`
- `support/refund`：退款金额校验辅助

## 引导词

### 完整流程

- 收钱吧退款
- 订单退款
- refund
- 退钱
- /refund
- 部分退款
- 全额退款
- /upay/v2/refund
- partial refund
- 退款接口

### 单独模块

- 退款请求构建
- refund request
- 退款金额校验
- 累计退款
- 部分退款校验
- 退款号生成
- refund_request_no
- refund adapter

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/upay/v2/refund` |
| 请求方法 | POST |
| 核心参数 | `sn/client_sn`, `refund_request_no`, `refund_amount`, `operator` |

## 关键规则

- `refund_request_no` 必须唯一
- 多次部分退款累计金额不能超过原订单金额
- `REFUND_IN_PROGRESS` / `REFUND_FAIL_ERROR` 需要查询确认
- 最终状态可能为 `REFUNDED` 或 `PARTIAL_REFUNDED`

## 完整流程生成

至少生成以下内容：

1. `RefundRequest` / `RefundResponse`
2. `SqbRefundAdapter.refund(...)`
3. 可退余额校验模块
4. `refund_request_no` 生成策略
5. 查询确认 / 轮询确认逻辑
6. 无沙盒环境警告

## 单独模块生成

### 模块：退款请求构建

只生成退款 DTO 与请求发送逻辑。

### 模块：退款金额校验

只生成可退余额计算、累计退款校验逻辑。

### 模块：退款号生成

只生成唯一退款请求号生成规则。

## 生成规则

1. 必须引用共享签名模块
2. 必须生成退款金额校验逻辑
3. 必须生成 `refund_request_no` 唯一性策略
4. 必须支持异步退款结果确认
5. 必须保留无沙盒环境警告
