---
name: sqb-pay
description: "[后端项目使用]收钱吧 B扫C 付款码支付接口技能。用于生成付款码支付的分层适配代码。当用户提到收钱吧支付、付款码支付、扫码收款、B扫C、/pay 时触发。"
version: "2.0"
tags: [payment, barcode, b2c, pay, adapter]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧付款码支付接口

## 分层定位

完整流程生成时，本 skill 应输出：

- `protocol/dto/payment`：支付请求与响应 DTO
- `protocol/security`：签名模块引用
- `adapter/payment`：`SqbPaymentAdapter`
- `support/status`：三层状态判定
- `support/polling`：支付轮询策略
- `bootstrap/facade`：支付接入 Facade 或服务骨架

## 引导词

### 完整流程

- 收钱吧支付
- 付款码支付
- 扫码收款
- B扫C
- shouqianba pay
- /pay
- 被扫支付
- barcode payment
- /upay/v2/pay
- B2C payment
- barcode pay

### 单独模块

- 支付请求构建
- pay request
- 订单号生成
- client_sn 生成
- 有密支付处理
- 密码支付
- payment adapter
- payment facade

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/upay/v2/pay` |
| 请求方法 | POST |
| 核心参数 | `client_sn`, `total_amount`, `dynamic_id`, `subject`, `operator` |

## 交易结果判定

- 第一层：`result_code`
- 第二层：`biz_response.result_code`
- 第三层：`order_status`

最终状态：

- `PAID`
- `PAY_CANCELED`

非最终状态：

- `CREATED`
- `PAY_ERROR`

## 完整流程生成

至少生成以下内容：

1. `PayRequest` / `PayResponse`
2. `SqbPaymentAdapter.pay(...)`
3. `SqbStatusParser` 或对共享状态模块的引用
4. `PAY_POLLING_CONFIG` 的引用
5. `SqbPaymentFacade` 或等价服务骨架
6. 无沙盒环境警告

推荐输出目录：

```text
protocol/dto/payment/
adapter/payment/
support/status/
support/polling/
bootstrap/facade/
```

## 单独模块生成

### 模块：支付请求构建

只生成请求 DTO、请求体构建与签名调用。

### 模块：client_sn 生成

只生成订单号生成策略，不生成 HTTP 调用。

### 模块：有密支付处理

只生成等待顾客输入密码、轮询等待与超时提示逻辑。

## 生成规则

1. 必须引用共享签名模块，不得内联重复签名实现
2. 必须引用三层状态判定模块
3. 非最终状态必须接入轮询
4. 必须保留 `client_sn` 全局唯一性说明
5. 必须保留无沙盒环境警告
