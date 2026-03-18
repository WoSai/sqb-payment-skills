---
name: sqb-refund
description: "[后端项目使用]收钱吧退款接口技能。用于对已支付订单进行全额或部分退款。当用户提到收钱吧退款、订单退款、refund、退钱、/refund时触发。"
---

# 收钱吧退款接口

## 引导词

- 收钱吧退款
- 订单退款
- refund
- 退钱
- /refund
- 部分退款
- 全额退款

## 概述

对已支付成功的订单进行退款操作。支持全额退款和部分退款。退款为异步操作，提交后需通过查询接口确认退款结果。

## 前置条件

- 已完成终端激活（sqb-activate），持有 `terminal_sn` 和 `terminal_key`
- 原订单状态为 `PAID`（已支付）
- API 域名：`https://vsi-api.shouqianba.com`

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/upay/v2/refund` |
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
| refund_request_no | string | Y | 退款请求号，**商户系统内唯一** |
| refund_amount | string | Y | 退款金额，单位为**分** |
| operator | string | Y | 操作员 |
| refund_reason | string | N | 退款原因 |

## 请求示例

```json
{
    "terminal_sn": "10298371039",
    "sn": "7892840250140845",
    "refund_request_no": "REF20230615143052001",
    "refund_amount": "100",
    "operator": "cashier_01",
    "refund_reason": "顾客要求退款"
}
```

## 响应参数

| 参数 | 说明 |
|---|---|
| sn | 收钱吧订单号 |
| client_sn | 商户订单号 |
| status | 订单状态 |
| order_status | 订单状态 |
| total_amount | 原订单金额（分） |
| net_amount | 实收金额（分） |
| refunded_amount | 累计已退款金额（分） |
| finish_time | 退款完成时间 |

## 响应示例

```json
{
    "result_code": "200",
    "biz_response": {
        "result_code": "REFUND_SUCCESS",
        "data": {
            "sn": "7892840250140845",
            "client_sn": "20230615143052001",
            "status": "REFUNDED",
            "order_status": "REFUNDED",
            "total_amount": "100",
            "net_amount": "0",
            "refunded_amount": "100",
            "finish_time": "1686820252000"
        }
    }
}
```

## 退款结果判定

### biz_response.result_code

| result_code | 含义 | 处理 |
|---|---|---|
| `REFUND_SUCCESS` | 退款成功 | 检查 order_status 确认 |
| `REFUND_FAIL` | 退款失败 | 根据错误信息处理 |
| `REFUND_IN_PROGRESS` | 退款处理中 | 启动查询轮询 |
| `REFUND_FAIL_ERROR` | 退款失败（不确定） | 启动查询轮询 |

### 退款后的 order_status

| order_status | 含义 |
|---|---|
| `REFUNDED` | 全额退款成功 |
| `PARTIAL_REFUNDED` | 部分退款成功 |
| `REFUND_ERROR` | 退款异常，需查询确认 |

## 部分退款

- 退款金额可小于原订单金额，实现部分退款
- 多次部分退款的累计金额不能超过原订单金额
- 部分退款后 order_status 变为 `PARTIAL_REFUNDED`
- 全额退款后 order_status 变为 `REFUNDED`

## 常见退款失败原因

| 原因 | 说明 | 解决方案 |
|---|---|---|
| 余额不足 | 顾客支付渠道余额不足以退款 | 提示顾客充值后重试 |
| 超过退款期限 | 超过 3 个月退款时限 | 线下处理 |
| 订单状态不允许 | 订单非 PAID 状态 | 先查询确认订单状态 |
| 退款金额超限 | 退款金额大于可退金额 | 检查已退款金额 |
| 重复退款请求号 | refund_request_no 重复 | 更换退款请求号 |

## 陷阱与注意事项

1. **退款是异步的**—— 收到 `REFUND_IN_PROGRESS` 时需轮询查询最终结果
2. **refund_request_no 唯一性**—— 每次退款请求必须使用唯一的退款请求号
3. **累计退款金额**—— 多次退款时注意累计金额不超过原订单金额
4. **退款到账时间**—— 不同渠道到账时间不同，微信通常即时，银行卡可能 1-3 天
5. **测试后务必退款**—— 因无沙盒环境，测试产生的交易必须退款

## 生成规则

当生成退款接口代码时，必须包含：
1. terminal 级别签名逻辑
2. refund_request_no 唯一性生成逻辑
3. 退款金额校验（不超过可退金额）
4. 退款结果判定（含异步轮询）
5. 退款失败的错误处理

## 代码示例

见 `reference/` 目录：
- `RefundExample.java` — Java 示例（OkHttp + Jackson）
- `refund_example.py` — Python 示例（requests）
