---
name: sqb-callback-verify
description: "收钱吧回调 RSA 验签工具。当用户需要单独生成回调验签、RSA 验签、公钥加载逻辑时触发。"
version: "1.0"
tags: [callback, verify, rsa, signature, security]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧回调 RSA 验签

## 引导词

- 回调验签
- RSA 验签
- SHA256WithRSA
- callback verify
- 收钱吧公钥
- 公钥验签
- 签名验证
- 回调签名校验
- notify 验签

## 概述

收钱吧异步回调（notify）使用 RSA SHA256WithRSA 非对称签名验证，与请求接口的 MD5 签名方式**完全不同**。验签是防止资金损失的最后一道防线，**不可省略**。

## 验签算法

### 请求签名 vs 回调验签

| 维度 | 请求签名 | 回调验签 |
|---|---|---|
| 算法 | MD5（对称） | RSA SHA256WithRSA（非对称） |
| 密钥 | terminal_key（商户持有） | 收钱吧 RSA 公钥（公开） |
| Authorization 格式 | `{sn} {md5_hex}` | `{terminal_sn} {base64_signature}` |
| 用途 | 商户向收钱吧证明身份 | 收钱吧向商户证明回调真实性 |

### 验签流程

```
1. 提取 Authorization header
2. split(" ", 2) → terminal_sn + base64_signature
3. Base64 解码 signature
4. 加载收钱吧 RSA 公钥（PEM 格式）
5. SHA256WithRSA 验证：publicKey.verify(signature, body_bytes)
6. 验证失败 → 返回 403，拒绝处理
```

### 公钥管理

- 公钥来源：从收钱吧服务商平台获取
- 存储方式：配置文件或密钥管理服务（KMS / Vault）
- 建议启动时加载并缓存，避免每次请求读文件
- 支持公钥轮换（配置化切换）

## 陷阱与注意事项

1. **验签对象是原始字节流**——不要先 JSON 解析再验签，必须用 request body 的原始 bytes
2. **Base64 解码签名**——Authorization 头中的签名是 Base64 编码的，需要先解码
3. **不可省略验签**——验签是防止伪造回调的唯一手段，省略验签等于放弃安全防线
4. **RSA 非 MD5**——回调验签使用 RSA 非对称签名，不要误用 MD5

## 生成规则

当用户需要单独生成回调验签模块时，**必须**包含：

1. `loadSqbPublicKey()` 函数：从 PEM 文件加载收钱吧 RSA 公钥，支持缓存
2. `verifySignatureRsa(bodyBytes, authHeader)` 函数：
   - 从 Authorization 头 split(" ", 2) 提取 terminal_sn 和 Base64 签名
   - Base64 解码签名
   - SHA256WithRSA 算法验证
   - 验证失败返回 false
3. ⚠️ 注释：验签是防止资金损失的最后一道防线，不可省略
4. ⚠️ 注释：验签对象是 HTTP body 的原始字节流，不要先解析 JSON
5. 异常处理：验签过程中的任何异常都应视为验签失败

## 代码示例

见 `reference/` 目录：
- `CallbackVerifyExample.java` — Java RSA 验签工具
- `callback_verify_example.py` — Python RSA 验签工具
