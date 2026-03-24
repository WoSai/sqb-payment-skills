# 收钱吧后端技能包（sqb-api-skills）

本目录包含收钱吧支付场景的后端 API 对接技能，覆盖 B扫C（付款码支付）和 C扫B（预下单）两种场景。

## 技能列表

| 技能 | 说明 | 触发词示例 |
|---|---|---|
| [sqb-activate](./sqb-activate/) | 终端激活 | "收钱吧激活"、"终端激活" |
| [sqb-checkin](./sqb-checkin/) | 终端签到（含密钥轮换容灾） | "收钱吧签到"、"终端签到" |
| [sqb-pay](./sqb-pay/) | B扫C 付款码支付 | "收钱吧支付"、"付款码支付"、"B扫C" |
| [sqb-precreate](./sqb-precreate/) | C扫B 预下单（二维码支付） | "收钱吧预下单"、"C扫B"、"二维码支付" |
| [sqb-query](./sqb-query/) | 订单查询 | "收钱吧查询"、"订单查询" |
| [sqb-refund](./sqb-refund/) | 退款（支持部分退款） | "收钱吧退款"、"订单退款"、"部分退款" |
| [sqb-cancel](./sqb-cancel/) | 撤单/冲正 | "收钱吧撤单"、"冲正"、"cancel" |
| [sqb-notify](./sqb-notify/) | 回调通知（RSA 验签） | "收钱吧回调"、"支付通知" |

## 跨接口共享模块 Skill

以下独立 Skill 封装了跨接口通用的功能模块，可单独触发生成对应模块代码：

| 技能 | 说明 | 触发词示例 |
|---|---|---|
| [sqb-signing](./sqb-signing/) | MD5 请求签名工具 | "收钱吧签名"、"MD5签名"、"Authorization头" |
| [sqb-status-parsing](./sqb-status-parsing/) | 三层状态判定 | "三层状态判定"、"状态解析"、"order_status判定" |
| [sqb-polling](./sqb-polling/) | 参数化轮询框架 | "轮询框架"、"polling"、"轮询策略" |
| [sqb-callback-verify](./sqb-callback-verify/) | RSA 回调验签 | "RSA验签"、"回调验签"、"公钥验签" |

## 模块化生成

每个接口 Skill 支持两种生成模式：

1. **完整流程模式**（默认）：用户请求完整功能时，生成端到端的实现代码
2. **模块化模式**：用户仅请求特定模块时（如"支付请求构建"、"退款金额校验"），只生成对应模块代码

模式由用户提示词自动判定。各 SKILL.md 的「引导词」章节中，「完整流程」子节触发完整生成，「单独模块」子节触发模块化生成。

## 共享工具类

`shared-reference/` 目录包含跨 skill 共享的核心代码模板：

| 文件 | 说明 | 被引用的 skill |
|---|---|---|
| `SqbSignUtil` / `sqb_sign_util.py` | MD5 签名工具 | 全部 |
| `SqbStatusUtil` / `sqb_status_util.py` | 三层状态判定 | pay, precreate, query, refund, cancel |
| `SqbPollingUtil` / `sqb_polling_util.py` | 参数化轮询框架 | pay, precreate, query |

> 生成代码时直接引用这些共享实现，不要自行重新编写。

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
- `PAY_SUCCESS` / `PAY_FAIL` / `PAY_IN_PROGRESS` / `PRECREATE_SUCCESS` / `REFUND_SUCCESS` / `CANCEL_SUCCESS` 等

### 推荐调用顺序

```
sqb-activate → sqb-checkin → sqb-pay/sqb-precreate → sqb-query → sqb-refund/sqb-cancel
```
