---
name: sqb-activate
description: "[后端项目使用]收钱吧终端激活接口技能。用于生成终端激活的分层适配代码。当用户提到收钱吧激活、终端激活、activate terminal、激活码、设备注册时触发。"
version: "2.0"
tags: [payment, terminal, activate, adapter]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧终端激活接口

## 分层定位

完整流程生成时，本 skill 应输出：

- `protocol/dto`：激活请求与响应 DTO
- `protocol/security`：vendor 签名调用
- `adapter/terminal`：`SqbTerminalActivateAdapter`
- `bootstrap`：配置与终端激活入口骨架

## 引导词

### 完整流程

- 收钱吧激活
- 终端激活
- activate terminal
- 激活码
- 设备注册
- sqb-activate
- terminal activate
- /terminal/activate
- 设备激活

### 单独模块

- vendor签名
- vendor级别签名
- 激活请求构建
- activate request
- terminal_key存储
- 密钥持久化

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/terminal/activate` |
| 请求方法 | POST |
| 签名 | `Authorization: {vendor_sn} {MD5(request_body + vendor_key)}` |

## 核心参数

- `app_id`
- `code`
- `device_id`
- `terminal_sn`
- `terminal_key`
- `vendor_sn`

## 完整流程生成

当用户要求完整接入时，生成内容至少包括：

1. `ActivateRequest` / `ActivateResponse`
2. 对 vendor 级别签名模块的引用
3. `SqbTerminalActivateAdapter.activate(...)`
4. `terminal_key` 持久化接口或存储占位
5. `SqbConfig` 或等价配置骨架

推荐输出目录：

```text
protocol/dto/terminal/
adapter/terminal/
bootstrap/config/
```

## 单独模块生成

### 模块：Vendor 级别签名

生成 `protocol/security` 层能力，强调仅激活接口使用 `vendor_sn / vendor_key`。

### 模块：激活请求构建

只生成请求 DTO 和 HTTP 请求构建逻辑，不生成持久化与控制器。

### 模块：terminal_key 存储

只生成存储接口 / 仓储占位，不生成完整业务流程。

## 生成规则

1. 必须包含 vendor 级别签名逻辑
2. 必须包含 `terminal_sn`、`terminal_key` 解析
3. 必须包含持久化接口或占位
4. 必须注明激活码一次性使用
5. 必须注明 `device_id` 唯一性
