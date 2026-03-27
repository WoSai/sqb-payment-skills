---
name: sqb-callback-verify
description: "收钱吧回调 RSA 验签模块。用于生成 protocol/security 层中的公钥加载、SHA256WithRSA 验签与回调真实性校验能力。"
version: "2.0"
tags: [callback, verify, rsa, protocol, security]
globs: ["**/*.java", "**/*.py"]
---

# 收钱吧回调 RSA 验签

## 分层定位

本 skill 属于 `protocol/security` 层。

它负责生成：

- PEM 公钥加载
- `verifySignatureRsa(bodyBytes, authHeader)`
- 回调签名解析

它不负责：

- 回调路由分发
- 业务订单更新
- 幂等落库

## 引导词

### 完整流程

- 回调验签
- RSA 验签
- SHA256WithRSA
- callback verify
- 收钱吧公钥
- 公钥验签
- 签名验证
- 回调签名校验
- notify 验签

### 单独模块

- public key loader
- protocol callback security

## 验签算法

| 维度 | 请求签名 | 回调验签 |
|---|---|---|
| 算法 | MD5 | RSA SHA256WithRSA |
| 密钥 | terminal_key | 收钱吧 RSA 公钥 |
| Authorization | `{sn} {md5_hex}` | `{terminal_sn} {base64_signature}` |

## 目标输出

### 完整流程生成

完整回调处理流程中，本 skill 应被引用到 `protocol/security` 层，并供 `sqb-notify` 使用。

### 单独模块生成

只生成公钥加载和验签模块，不生成控制器。

## 生成规则

1. 必须提供 `loadSqbPublicKey()`
2. 必须提供 `verifySignatureRsa(bodyBytes, authHeader)`
3. 必须从 Authorization 头中拆出 `terminal_sn` 和 Base64 签名
4. 必须使用 HTTP body 原始字节流进行验签
5. 验签失败必须返回 false 或直接拒绝请求
6. 必须注明：验签不可省略，是资金安全最后防线

## 代码示例

见 `reference/` 目录：

- `CallbackVerifyExample.java`
- `callback_verify_example.py`
