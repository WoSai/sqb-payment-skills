---
name: sqb-precreate
description: "[后端项目使用]收钱吧 C扫B 预下单接口技能。用于生成二维码支付的分层适配代码。"
version: "2.0"
tags: [payment, qrcode, c2b, precreate, adapter]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧 C扫B 预下单接口

## 分层定位

完整流程生成时，本 skill 应输出：

- `protocol/dto/payment`：预下单请求与响应 DTO
- `adapter/payment`：`SqbPrecreateAdapter`
- `support/status`：状态判定
- `support/polling`：预下单轮询策略
- `bootstrap/facade`：二维码支付接入骨架

## 引导词

### 完整流程

- 收钱吧预下单
- C扫B
- 二维码支付
- QR支付
- precreate
- 扫码付
- 顾客扫码
- 主扫支付

### 单独模块

- 预下单请求构建
- precreate request
- 二维码处理
- QR code
- qr_code 提取
- precreate adapter

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/upay/v2/precreate` |
| 请求方法 | POST |
| 核心参数 | `client_sn`, `total_amount`, `payway`, `subject`, `operator` |

## 关键规则

- `payway` 在预下单场景中为必填
- 需要从响应中提取 `qr_code`
- `order_status` 为 `IN_QUEUE` / `CREATED` / `PAY_ERROR` 时必须轮询

## 完整流程生成

至少生成以下内容：

1. `PrecreateRequest` / `PrecreateResponse`
2. `SqbPrecreateAdapter.precreate(...)`
3. `qr_code` 提取逻辑
4. `PRECREATE_POLLING_CONFIG` 的引用
5. 面向前端的二维码结果对象或 Facade
6. 无沙盒环境警告

## 单独模块生成

### 模块：预下单请求构建

只生成请求 DTO 和请求发送逻辑。

### 模块：二维码处理

只生成 `qr_code` 提取、返回结构和对前端的交付模型。

## 生成规则

1. 必须保留 `payway` 必填说明
2. 必须引用共享签名模块
3. 必须引用状态判定与轮询模块
4. 必须输出 `qr_code`
5. 必须保留无沙盒环境警告
