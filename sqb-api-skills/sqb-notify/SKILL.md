---
name: sqb-notify
description: "[后端项目使用]收钱吧异步回调通知处理技能。用于接收和处理收钱吧的交易状态变化通知。当用户提到收钱吧回调、支付通知、异步通知、notify、webhook时触发。"
---

# 收钱吧异步回调通知

## 引导词

- 收钱吧回调
- 支付通知
- 异步通知
- notify
- webhook
- 回调处理

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
- **重试策略**: 若商户返回非 200 状态码，收钱吧会进行多次重试

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

## 回调验签

收到回调后，应验证请求的合法性：

1. 使用本地存储的 `terminal_key` 验证签名
2. 签名位于请求头 `Authorization` 中
3. 验签方式与请求签名相同：`MD5(request_body + terminal_key)`

```python
# 伪代码
def verify_callback(request):
    auth_header = request.headers['Authorization']
    terminal_sn, received_sign = auth_header.split(' ', 1)

    body = request.body  # 原始请求体
    terminal_key = get_terminal_key(terminal_sn)  # 从存储中获取

    expected_sign = md5(body + terminal_key)
    return received_sign == expected_sign
```

## 回调响应

商户收到回调后应返回：

```json
200 OK
```

返回 HTTP 200 状态码表示收到通知。非 200 状态码会触发重试。

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

当生成回调处理代码时，必须包含：
1. HTTP POST 接口接收回调
2. 签名验证逻辑
3. 幂等处理（防重复）
4. 订单状态更新逻辑
5. 返回 200 响应
6. 异常处理与日志记录

## 代码示例

见 `reference/` 目录：
- `NotifyExample.java` — Java 示例（Spring Boot 风格）
- `notify_example.py` — Python 示例（Flask）
