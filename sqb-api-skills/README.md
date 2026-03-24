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

## 两种生成模式

每个接口 Skill 同时支持**完整流程生成**和**单独模块生成**，开发者按需选择即可。

### 完整流程生成（默认）

使用通用触发词（如"收钱吧支付"、"帮我接入退款接口"），AI 生成该接口从签名到异常处理的**完整端到端实现**。适合从零开始接入一个接口。

### 单独模块生成

使用模块级触发词（如"支付请求构建"、"退款金额校验"），AI **只生成对应模块**的代码片段。适合已有项目中补充或替换某个功能环节。

每个 SKILL.md 的「引导词」章节分为两组：

- **「完整流程」** — 触发完整代码生成
- **「单独模块」** — 触发对应模块的代码生成

### 各接口可用模块一览

| 接口 Skill | 可单独生成的模块 |
|---|---|
| sqb-pay | 支付请求构建、订单号(client_sn)生成、有密支付处理 |
| sqb-precreate | 预下单请求构建、二维码(qr_code)提取与渲染 |
| sqb-refund | 退款请求构建、退款金额校验(累计退款)、退款号(refund_request_no)生成 |
| sqb-query | 查询请求构建、订单状态判定(最终/非最终)、轮询框架集成 |
| sqb-cancel | 撤单请求构建、撤单结果判定(四种结果码)、撤单后查询确认 |
| sqb-activate | Vendor 级别签名、激活请求构建、terminal_key 持久化存储 |
| sqb-checkin | 签到请求构建、密钥轮换逻辑、双 key 容灾机制 |
| sqb-notify | RSA 回调验签、幂等处理(防重复)、回调分发逻辑、公钥管理 |

### 示例对比

```
# 完整流程模式 → 生成支付接口的全部代码（签名 + 请求 + 状态判定 + 轮询 + 异常处理）
"帮我用 Java 接入收钱吧付款码支付"

# 单独模块模式 → 只生成请求构建部分的代码
"帮我生成收钱吧支付请求构建模块"

# 单独模块模式 → 只生成 client_sn 生成逻辑
"帮我实现收钱吧订单号生成"
```

> 模式由 AI 根据提示词自动判定，无需手动切换。

## 跨接口共享模块 Skill

以下 4 个通用功能被封装为独立 Skill，不绑定任何特定接口，适合在已有项目中直接补充某项通用能力：

| 技能 | 功能 | 触发词示例 | 典型场景 |
|---|---|---|---|
| [sqb-signing](./sqb-signing/) | MD5 请求签名 + Authorization 头 | "收钱吧签名"、"MD5签名" | 已有 HTTP 客户端，只缺签名 |
| [sqb-status-parsing](./sqb-status-parsing/) | 三层状态判定 | "三层状态判定"、"状态解析" | 已有请求逻辑，需补充响应解析 |
| [sqb-polling](./sqb-polling/) | 参数化轮询框架 | "轮询框架"、"polling" | 需要通用轮询，不限于特定接口 |
| [sqb-callback-verify](./sqb-callback-verify/) | RSA SHA256WithRSA 回调验签 | "RSA验签"、"回调验签" | 已有回调接口，只需验签逻辑 |

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
