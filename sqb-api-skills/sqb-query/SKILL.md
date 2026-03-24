---
name: sqb-query
description: "[后端项目使用]收钱吧订单查询接口技能。用于查询订单实时状态和支付结果轮询。当用户提到收钱吧查询、订单查询、交易查询、query order、/query时触发。"
version: "1.1"
tags: [payment, query, polling, order-status]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧订单查询接口

## 引导词

### 完整流程
- 收钱吧查询
- 订单查询
- 交易查询
- query order
- /query
- 查询订单状态
- 轮询
- /upay/v2/query
- order status
- 支付结果查询

### 单独模块
- 查询请求构建 / query request（→ 仅生成查询请求模块）
- 订单状态判定 / status判定 / 最终状态判定（→ 仅生成状态判定模块）
- 轮询框架集成 / polling集成（→ 仅生成轮询集成模块）

## 概述

查询订单的实时状态。用于：
1. 付款后轮询确认最终结果
2. 主动查询历史订单状态
3. 退款前确认订单状态

## 前置条件

- 已完成终端激活（sqb-activate），持有 `terminal_sn` 和 `terminal_key`
- API 域名：`https://vsi-api.shouqianba.com`

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/upay/v2/query` |
| 请求方法 | POST |
| Content-Type | `application/json; charset=utf-8` |
| API 域名 | `https://vsi-api.shouqianba.com` |

## 签名方式

```
Authorization: {terminal_sn} {MD5(request_body + terminal_key)}
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| terminal_sn | string | Y | 终端序列号 |
| sn | string | N | 收钱吧订单号（sn 和 client_sn 二选一） |
| client_sn | string | N | 商户订单号（sn 和 client_sn 二选一） |

> 注意：`sn` 和 `client_sn` 至少传一个，同时传入时以 `sn` 为准。

## 请求示例

```json
{
    "terminal_sn": "10298371039",
    "client_sn": "20230615143052001"
}
```

## 响应参数

| 参数 | 说明 |
|---|---|
| sn | 收钱吧订单号 |
| client_sn | 商户订单号 |
| trade_no | 支付渠道交易号 |
| status | 订单状态 |
| order_status | 同 status |
| total_amount | 交易总金额（分） |
| net_amount | 实收金额（分） |
| finish_time | 交易完成时间 |
| subject | 交易简介 |
| operator | 操作员 |
| refunded_amount | 已退款金额（分） |

## 响应示例

```json
{
    "result_code": "200",
    "biz_response": {
        "result_code": "SUCCESS",
        "data": {
            "sn": "7892840250140845",
            "client_sn": "20230615143052001",
            "trade_no": "2023061522001456781234567890",
            "status": "PAID",
            "order_status": "PAID",
            "total_amount": "100",
            "net_amount": "97",
            "finish_time": "1686816652000",
            "subject": "星巴克咖啡",
            "operator": "cashier_01"
        }
    }
}
```

## 订单状态说明

| order_status | 含义 | 是否最终状态 |
|---|---|---|
| `CREATED` | 订单已创建 | 否 |
| `PAID` | 支付成功 | **是** |
| `PAY_CANCELED` | 支付失败/已撤销 | **是** |
| `PAY_ERROR` | 支付异常 | 否 |
| `REFUNDED` | 全额退款 | **是** |
| `PARTIAL_REFUNDED` | 部分退款 | **是** |
| `REFUND_ERROR` | 退款异常 | 否 |
| `CANCELED` | 已撤销 | **是** |
| `CANCEL_ERROR` | 撤销异常 | 否 |

## 轮询查询模式

当用于支付结果轮询时，建议实现如下策略：

```python
# 伪代码
elapsed = 0
while True:
    result = query_order(client_sn)
    order_status = result['biz_response']['data']['order_status']

    # 最终状态，返回结果
    if order_status in ['PAID', 'PAY_CANCELED', 'REFUNDED', 'PARTIAL_REFUNDED']:
        return result

    # 计算等待时间
    if elapsed < 60:
        wait_time = 3   # 前60秒每3秒查询
    else:
        wait_time = 10  # 之后每10秒查询

    sleep(wait_time)
    elapsed += wait_time

    # 超时处理（建议120秒）
    if elapsed > 120:
        notify_operator("交易超时，请人工确认")
        break
```

## 陷阱与注意事项

1. **查询不改变订单状态**—— 查询是安全的只读操作
2. **非最终状态必须继续查询**—— 不能将 CREATED 或 PAY_ERROR 当作失败
3. **网络超时不代表交易失败**—— 查询超时时应重试查询，而非假定失败
4. **sn 优先于 client_sn**—— 两个都传时以 sn 为准

## 生成规则

当生成查询接口代码时，**必须**包含：
1. 签名逻辑引用 `shared-reference/SqbSignUtil`，不要自行编写签名实现
2. 支持 sn 和 client_sn 两种查询方式
3. 订单状态判定引用 `shared-reference/SqbStatusUtil`（最终/非最终状态）
4. 当用于轮询时，引用 `shared-reference/SqbPollingUtil` 的轮询框架
5. 超时处理机制
6. **在类/模块级别注释中标注**：`⚠️ 警告：收钱吧没有沙盒环境，此代码查询的是真实交易`

## 模块化生成

本技能支持单独生成以下模块。当用户 prompt 中包含模块关键词时，仅生成对应模块代码，不生成完整流程。无模块关键词时，按上方"生成规则"生成完整代码。

> 签名、三层状态判定、轮询框架等跨接口共享模块请使用对应的独立 Skill（sqb-signing、sqb-status-parsing、sqb-polling）。

### 模块：查询请求构建

**触发关键词**："查询请求构建"、"query request"、"构建查询报文"

**生成规则**：
1. 构建 JSON 请求体，包含 terminal_sn 和 sn/client_sn（二选一，sn 优先）
2. 调用签名工具计算 Authorization 头
3. POST 请求到 `/upay/v2/query`，Content-Type: `application/json; charset=utf-8`
4. 返回原始 JSON 响应
5. ⚠️ 无沙盒环境警告

**参考代码（Java）**：
```java
// 查询请求构建（需配合 SqbSignUtil 签名工具使用）
ObjectNode body = mapper.createObjectNode();
body.put("terminal_sn", terminalSn);
if (sn != null && !sn.isEmpty()) {
    body.put("sn", sn);               // sn 优先
} else {
    body.put("client_sn", clientSn);   // 备选 client_sn
}

String bodyStr = mapper.writeValueAsString(body);
String sign = SqbSignUtil.md5Sign(bodyStr, terminalKey);

Request request = new Request.Builder()
    .url("https://vsi-api.shouqianba.com/upay/v2/query")
    .addHeader("Authorization", terminalSn + " " + sign)
    .addHeader("Content-Type", "application/json; charset=utf-8")
    .post(RequestBody.create(bodyStr, JSON_TYPE))
    .build();
```

**参考代码（Python）**：
```python
# 查询请求构建（需配合 sqb_sign_util 签名工具使用）
body = {"terminal_sn": terminal_sn}
if sn:
    body["sn"] = sn               # sn 优先
else:
    body["client_sn"] = client_sn  # 备选 client_sn

body_str = json.dumps(body, ensure_ascii=False)
sign = md5_sign(body_str, terminal_key)
headers = {
    "Authorization": f"{terminal_sn} {sign}",
    "Content-Type": "application/json; charset=utf-8",
}
resp = requests.post(
    "https://vsi-api.shouqianba.com/upay/v2/query",
    data=body_str.encode("utf-8"),
    headers=headers,
    timeout=30,
)
```

### 模块：订单状态判定

**触发关键词**："状态判定"、"最终状态判定"、"order_status判定"、"final status"

**生成规则**：
1. 三层判定逻辑：result_code → biz_response.result_code → order_status
2. 最终状态集合：PAID、PAY_CANCELED、REFUNDED、PARTIAL_REFUNDED、CANCELED
3. 非最终状态需继续轮询：CREATED、PAY_ERROR、CANCEL_ERROR、REFUND_ERROR
4. 引用 `shared-reference/SqbStatusUtil`

**参考代码（Java）**：
```java
// 订单状态判定
Set<String> FINAL_STATUSES = Set.of(
    "PAID", "PAY_CANCELED", "REFUNDED", "PARTIAL_REFUNDED", "CANCELED");

public boolean isFinalStatus(String orderStatus) {
    return FINAL_STATUSES.contains(orderStatus);
}
```

**参考代码（Python）**：
```python
# 订单状态判定
FINAL_STATUSES = {"PAID", "PAY_CANCELED", "REFUNDED", "PARTIAL_REFUNDED", "CANCELED"}

def is_final_status(order_status: str) -> bool:
    return order_status in FINAL_STATUSES
```

### 模块：轮询框架集成

**触发关键词**："轮询集成"、"polling集成"、"查询轮询"、"poll query"

**生成规则**：
1. 引用 `shared-reference/SqbPollingUtil` 轮询框架
2. 将查询请求作为回调函数传入轮询器
3. 配置轮询参数：初始间隔、频率切换时间、长间隔、超时时间
4. 处理轮询超时（提示人工确认）

**参考代码（Java）**：
```java
// 轮询框架集成：将查询作为轮询回调使用
SqbPollingUtil.PollingConfig config = new SqbPollingUtil.PollingConfig(60, 3, 10, 120);
SqbPollingUtil.PollingResult result = SqbPollingUtil.pollUntilFinal(
    () -> queryOrderStatus(clientSn), config, null);

if (result.isTimeout()) {
    log.warn("查询超时，请人工确认: clientSn={}", clientSn);
}
```

**参考代码（Python）**：
```python
# 轮询框架集成：将查询作为轮询回调使用
config = PollingConfig(phase1_duration=60, phase1_interval=3, phase2_interval=10, total_timeout=120)
result = poll_until_final(query_fn=lambda: query_order(client_sn), config=config)

if result.is_timeout:
    logger.warning(f"查询超时，请人工确认: client_sn={client_sn}")
```

## 代码示例

见 `reference/` 目录：
- `QueryExample.java` — Java 示例（含轮询，OkHttp + Jackson）
- `query_example.py` — Python 示例（含轮询，requests）
