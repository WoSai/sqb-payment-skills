# 收钱吧后端技能包（sqb-api-skills）

本目录包含收钱吧 B扫C（付款码支付）场景的后端 API 对接技能。

## 技能列表

| 技能 | 说明 | 触发词示例 |
|---|---|---|
| [sqb-activate](./sqb-activate/) | 终端激活 | "收钱吧激活"、"终端激活" |
| [sqb-checkin](./sqb-checkin/) | 终端签到 | "收钱吧签到"、"终端签到" |
| [sqb-pay](./sqb-pay/) | 付款码支付 | "收钱吧支付"、"付款码支付"、"B扫C" |
| [sqb-query](./sqb-query/) | 订单查询 | "收钱吧查询"、"订单查询" |
| [sqb-refund](./sqb-refund/) | 退款 | "收钱吧退款"、"订单退款" |
| [sqb-notify](./sqb-notify/) | 回调通知 | "收钱吧回调"、"支付通知" |

## 通用规范

### 请求协议

- 协议：HTTPS POST
- Content-Type: `application/json`
- 编码：UTF-8
- API 域名：`https://vsi-api.shouqianba.com`

### 签名方式

**激活接口**使用 vendor 级别签名：
```
Authorization: {vendor_sn} {MD5(request_body + vendor_key)}
```

**其他接口**使用 terminal 级别签名：
```
Authorization: {terminal_sn} {MD5(request_body + terminal_key)}
```

> 注意：sn 和签名之间有且仅有一个空格。request_body 必须是 UTF-8 编码的原始 JSON 字符串，签名时的字符串必须和实际发送的请求体完全一致。

### 响应格式

所有接口返回统一的 JSON 格式：

```json
{
    "result_code": "200",
    "biz_response": {
        "result_code": "PAY_SUCCESS",
        "data": { ... }
    }
}
```

**result_code**（通信级别）：
- `200`：通信成功，需继续判断 biz_response
- 非 `200`：通信失败（如签名错误、参数缺失等）

**biz_response.result_code**（业务级别）：
- `PAY_SUCCESS` / `PAY_FAIL` / `PAY_IN_PROGRESS` / `REFUND_SUCCESS` 等

### 推荐调用顺序

```
sqb-activate → sqb-checkin → sqb-pay → sqb-query → sqb-refund
```
