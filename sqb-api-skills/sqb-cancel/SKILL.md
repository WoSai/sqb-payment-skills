---
name: sqb-cancel
description: "[后端项目使用]收钱吧撤单/冲正接口技能。用于生成撤单适配器、撤单结果判定和查询确认逻辑。"
version: "2.0"
tags: [payment, cancel, reverse, adapter]
globs: ["**/*.java", "**/*.py"]
---

# 收钱吧撤单接口

## 分层定位

完整流程生成时，本 skill 应输出：

- `protocol/dto/cancel`
- `adapter/cancel`：`SqbCancelAdapter`
- `support/status`
- `support/polling` 或查询确认辅助

## 引导词

### 完整流程

- 收钱吧撤单
- 冲正
- cancel
- 交易撤销
- 撤单接口
- /upay/v2/cancel
- reverse payment
- cancel payment

### 单独模块

- 撤单请求构建
- cancel request
- cancel结果解析
- 撤单结果判定
- cancel查询确认
- cancel adapter

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/upay/v2/cancel` |
| 请求方法 | POST |
| 核心参数 | `terminal_sn`, `sn/client_sn`, `operator` |

## 完整流程生成

至少生成以下内容：

1. `CancelRequest` / `CancelResponse`
2. `SqbCancelAdapter.cancel(...)`
3. 撤单结果判定逻辑
4. 撤单后查询确认逻辑
5. 无沙盒环境警告

## 单独模块生成

### 模块：撤单请求构建

只生成 DTO 与请求调用。

### 模块：撤单结果判定

只生成业务结果码与 `order_status` 判断逻辑。

### 模块：撤单后查询确认

只生成撤单后 query adapter 的确认流程。

## 生成规则

1. 必须引用共享签名模块
2. 必须引用状态判定模块
3. 不确定结果必须进入查询确认
4. 必须保留无沙盒环境警告
