---
name: sqb-query
description: "[后端项目使用]收钱吧订单查询接口技能。用于查询订单实时状态和支付结果轮询。当用户提到收钱吧查询、订单查询、交易查询、query order、/query时触发。"
version: "1.1"
tags: [payment, query, polling, order-status]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧订单查询接口

## 引导词

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

## 代码示例

见 `reference/` 目录：
- `QueryExample.java` — Java 示例（含轮询，OkHttp + Jackson）
- `query_example.py` — Python 示例（含轮询，requests）
