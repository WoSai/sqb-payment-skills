---
name: sqb-signing
description: "收钱吧 MD5 请求签名工具。当用户需要单独生成签名逻辑、Authorization 头构建、请求签名时触发。"
version: "1.0"
tags: [signing, md5, authorization, utility]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧 MD5 请求签名

## 引导词

- 收钱吧签名
- MD5 签名
- 请求签名
- Authorization 头
- signing
- 签名工具
- sign util
- 签名逻辑
- 收钱吧 Authorization

## 概述

收钱吧所有 API 接口使用 MD5 签名机制进行身份验证。签名公式：`sign = MD5(request_body + key)`。签名值与序列号一起放入 HTTP Authorization 头中。

## 签名算法

### 公式

```
sign = MD5(request_body + key)
Authorization = {sn} {sign}
```

### 两种凭证

| 场景 | sn | key | 说明 |
|---|---|---|---|
| 终端激活 (`/terminal/activate`) | `vendor_sn` | `vendor_key` | 仅激活接口使用服务商凭证 |
| 其他所有接口 | `terminal_sn` | `terminal_key` | 激活后获得，签到后会更新 key |

### 关键约束

1. **request_body** 必须是 UTF-8 编码的原始 JSON 字符串
2. 签名时使用的字符串**必须和实际发送的请求体完全一致**（包括字段顺序、空格等）
3. MD5 输出为 **32 位小写十六进制**字符串
4. Authorization 头中 sn 和 sign 之间有且仅有**一个空格**
5. Content-Type 必须为 `application/json; charset=utf-8`

### 典型错误

- 签名时的 JSON 字符串与实际请求体不一致（分别序列化导致字段顺序不同）
- 忘记在 MD5 计算前拼接 key
- MD5 输出使用了大写（应为小写）
- Authorization 头中多了或少了空格

## 生成规则

当用户需要单独生成签名模块时，**必须**包含：

1. `md5Sign(bodyStr, key)` 函数：计算 MD5(body + key)，返回 32 位小写十六进制
2. `buildAuthorization(sn, bodyStr, key)` 函数：返回 `{sn} {sign}`
3. `serializeBody(body)` 函数：将请求参数序列化为 JSON 字符串（Python 使用 `ensure_ascii=False`）
4. ⚠️ 注释强调：序列化后的字符串同时用于签名和 HTTP 请求体，两者必须完全一致，不要分别序列化
5. 注释说明 sn 与 sign 之间有且仅有一个空格
6. 注释区分 vendor 凭证（仅激活）与 terminal 凭证（其他接口）的使用场景

## 代码示例

见 `reference/` 目录：
- `SqbSignUtil.java` — Java 签名工具类
- `sqb_sign_util.py` — Python 签名工具类
