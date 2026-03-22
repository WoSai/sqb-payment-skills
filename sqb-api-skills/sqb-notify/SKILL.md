---
name: sqb-notify
description: "[后端项目使用]收钱吧异步回调通知处理技能。用于接收和处理收钱吧的交易状态变化通知。当用户提到收钱吧回调、支付通知、异步通知、notify、webhook时触发。"
version: "1.1"
tags: [payment, notify, webhook, callback]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧异步回调通知

## 引导词

- 收钱吧回调
- 支付通知
- 异步通知
- notify
- webhook
- 回调处理
- callback handler
- 回调接口
- notify_url

## 概述

当交易状态发生变化时，收钱吧会主动向商户预设的回调地址发送 HTTP 通知。回调是对主动轮询的补充机制，不能完全替代主动查询。

## 前置条件

- 在支付请求中通过 `notify_url` 参数指定回调地址
- 回调地址必须是公网可访问的 HTTPS URL
- 服务端需要实现回调接收接口

## 回调机制

### 触发条件

以下状态变化会触发回调通知：
- 支付成功（PAID）
- 支付失败/撤销（PAY_CANCELED）
- 退款成功（REFUNDED / PARTIAL_REFUNDED）

### 回调方式

- **方法**: POST
- **Content-Type**: `application/json`
- **重试策略**: 若商户未返回 `success`，收钱吧按以下间隔重试：1秒、5秒、30秒、600秒（共 4 次重试）

## 回调报文示例

```json
{
    "terminal_sn": "10298371039",
    "sn": "7892840250140845",
    "client_sn": "20230615143052001",
    "trade_no": "2023061522001456781234567890",
    "status": "PAID",
    "order_status": "PAID",
    "total_amount": "100",
    "net_amount": "97",
    "subject": "星巴克咖啡",
    "finish_time": "1686816652000",
    "channel_finish_time": "1686816651000",
    "operator": "cashier_01",
    "reflect": ""
}
```

## 回调验签（安全关键，不可跳过）

> ⚠️ **强制要求**：生成代码时必须包含验签逻辑，不可作为可选项。验签是防止资金损失的最后一道防线。

收到回调后，**必须**验证请求的合法性，验签失败的请求必须直接拒绝（返回 403），不得处理任何业务逻辑。

### 验签方式：RSA SHA256WithRSA

1. 从 `Authorization` 请求头中提取签名值
2. 获取收钱吧 RSA 公钥（从配置文件或密钥管理服务加载）
3. 使用 `SHA256WithRSA` 算法，以收钱吧公钥验证 request_body 的签名
4. 验签失败立即返回 403，不处理业务逻辑

```python
# 伪代码
def verify_callback(request):
    auth_header = request.headers['Authorization']
    terminal_sn, received_sign_b64 = auth_header.split(' ', 1)

    body = request.body  # 原始请求体（UTF-8 字节流）
    public_key = load_sqb_public_key()  # 加载收钱吧 RSA 公钥

    # RSA SHA256WithRSA 验签
    signature_bytes = base64.b64decode(received_sign_b64)
    public_key.verify(signature_bytes, body, padding.PKCS1v15(), hashes.SHA256())
    return True  # 验签通过
```

### 公钥管理

- 收钱吧 RSA 公钥由服务商平台获取，应安全存储
- 建议使用配置文件或密钥管理服务（如 AWS KMS、Vault）管理公钥
- 公钥更换时需要及时更新，否则验签将失败

## 回调响应

商户收到回调后应返回纯文本：

```
success
```

返回 `success` 文本表示接收成功。返回其他内容或非 200 状态码会触发重试。

## 陷阱与注意事项

### 1. 回调不可靠，不能替代主动查询
网络问题、服务器宕机等都可能导致回调丢失。**必须同时实现主动轮询查询作为兜底**。

### 2. 回调可能重复
同一笔订单可能收到多次相同的回调通知，接收端必须做**幂等处理**：
- 收到回调后先查询本地订单状态
- 如果已经是最终状态，忽略重复回调
- 使用 sn 或 client_sn 作为幂等键

### 3. 回调顺序不保证
多次回调的到达顺序可能与事件发生顺序不一致，应以 order_status 为准而非到达顺序。

### 4. 验签防伪造
必须验证回调签名，防止伪造的回调通知导致资金风险。

## 生成规则

当生成回调处理代码时，**必须**包含以下全部内容（缺一不可）：
1. HTTP POST 接口接收回调
2. **RSA SHA256WithRSA 签名验证逻辑**（不可省略，不可留空待实现）
3. 验签失败立即返回 403，不处理业务
4. 幂等处理（防重复）
5. 订单状态更新逻辑
6. 返回 `success` 文本响应
7. 异常处理与日志记录

> ⚠️ 签名验证是防止伪造回调导致资金风险的最后一道防线。生成代码时**禁止**将验签留空待实现或标记为可选项。

## 代码示例

见 `reference/` 目录：
- `NotifyExample.java` — Java 示例（Spring Boot 风格）
- `notify_example.py` — Python 示例（Flask）
