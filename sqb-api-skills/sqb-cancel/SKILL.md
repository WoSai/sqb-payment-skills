---
name: sqb-cancel
description: "[后端项目使用]收钱吧撤单接口技能。用于撤销当天的交易订单。当用户提到收钱吧撤单、冲正、cancel、撤销交易、取消订单时触发。"
version: "1.1"
tags: [payment, cancel, void, reversal]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧撤单（冲正）接口

## 引导词

- 收钱吧撤单
- 冲正
- cancel
- 撤销交易
- 取消订单
- void
- 撤单接口
- /cancel

## 概述

撤单（冲正）用于撤销当天的交易订单。主要用于 pay 接口超时或状态不确定时保障资金安全，防止"商户以为失败但实际扣款成功"的情况。撤单为全额撤销，手续费也会全额退回。

## 前置条件

- 已完成终端激活（sqb-activate），持有 `terminal_sn` 和 `terminal_key`
- 原订单为当天交易（当日 00:00 后的交易）
- 原订单未进行过部分退款
- API 域名：`https://vsi-api.shouqianba.com`
- 协议：HTTPS POST，Content-Type: `application/json; charset=utf-8`

## 签名方式

```
Authorization: {terminal_sn} {MD5(request_body + terminal_key)}
```

> 注意：sn 和 sign 之间有且仅有一个空格。request_body 必须是 UTF-8 编码的原始 JSON 字符串，签名时的字符串必须和实际请求体完全一致（包括字段顺序、空格等）。签名逻辑请参考 `shared-reference/SqbSignUtil`。

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/upay/v2/cancel` |
| 请求方法 | POST |
| Content-Type | `application/json; charset=utf-8` |
| API 域名 | `https://vsi-api.shouqianba.com` |

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| terminal_sn | string | Y | 终端序列号 |
| sn | string | N | 收钱吧订单号（sn 和 client_sn 二选一） |
| client_sn | string | N | 商户订单号（sn 和 client_sn 二选一） |

> 注意：`sn` 和 `client_sn` 必须至少提供一个，推荐优先使用 `sn`。

## 请求示例

```json
{
    "terminal_sn": "10298371039",
    "sn": "7892840250140845"
}
```

## 响应参数

| 参数 | 说明 |
|---|---|
| sn | 收钱吧订单号 |
| client_sn | 商户订单号 |
| status | 订单状态 |
| order_status | 订单状态 |
| total_amount | 交易总金额（分） |
| net_amount | 实收金额（分） |
| finish_time | 撤单完成时间 |

## 响应示例

```json
{
    "result_code": "200",
    "biz_response": {
        "result_code": "CANCEL_SUCCESS",
        "data": {
            "sn": "7892840250140845",
            "client_sn": "20230615143052001",
            "status": "PAY_CANCELED",
            "order_status": "PAY_CANCELED",
            "total_amount": "100",
            "net_amount": "0",
            "finish_time": "1686816852000"
        }
    }
}
```

## 撤单结果判定（关键）

### 第一层：result_code（通信层）

| result_code | 含义 | 处理 |
|---|---|---|
| `200` | 通信成功 | 继续判断 biz_response |
| 非 `200` | 通信失败 | 根据错误码处理，可能需要重试 |

### 第二层：biz_response.result_code（业务层）

| result_code | 含义 | 处理 |
|---|---|---|
| `CANCEL_SUCCESS` | 撤销成功 | 交易已撤销，资金已退回 |
| `CANCEL_ERROR` | 撤销失败（不确定） | 需调用查询接口确认订单最终状态 |
| `CANCEL_ABORT_SUCCESS` | 中断支付成功 | 支付中的订单被成功中断 |
| `CANCEL_ABORT_ERROR` | 中断支付失败 | 需调用查询接口确认订单最终状态 |

> **重要**：收到 `CANCEL_ERROR` 或 `CANCEL_ABORT_ERROR` 时，**禁止**直接判定为撤单成功或失败，必须调用查询接口（sqb-query）确认订单最终状态。

## 使用场景

1. **Pay 接口超时**：调用 pay 接口超时，无法确认扣款结果时，立即发起撤单保障资金安全
2. **PAY_FAIL_ERROR（不确定失败）**：pay 返回 `PAY_FAIL_ERROR`，查询后仍无法确认最终状态时，发起撤单
3. **收银员手动取消**：收银员在当天交易记录中手动取消某笔交易
4. **防止资金损失**：防止"商户以为失败但实际扣款成功"导致顾客资金损失的情况

## 撤单 vs 退款

| 对比项 | 撤单（cancel） | 退款（refund） |
|---|---|---|
| 时间限制 | 仅限当天 | 通常 3 个月内 |
| 金额 | 全额撤销 | 支持部分退款 |
| 手续费 | 全额退回 | 可能不退手续费 |
| 主要用途 | 异常处理、资金安全保障 | 正常业务退款 |
| 已部分退款的订单 | **不可撤单** | 可继续退款 |

## 关键限制

1. **仅限当天订单**（当日 00:00 后的交易），跨天的交易只能走退款流程
2. **全额撤销**，不支持部分撤销
3. **已部分退款的订单不能撤单**，只能继续走退款流程
4. **手续费全额退回**，这是与退款的关键区别

## 撤单失败后的查询确认流程

```
1. 发起撤单请求
2. 判断 biz_response.result_code：
   ├── CANCEL_SUCCESS → 撤单成功，流程结束
   ├── CANCEL_ABORT_SUCCESS → 中断支付成功，流程结束
   ├── CANCEL_ERROR → 撤单结果不确定，进入步骤 3
   └── CANCEL_ABORT_ERROR → 中断结果不确定，进入步骤 3
3. 调用查询接口（sqb-query）确认订单最终状态
   ├── order_status = PAY_CANCELED → 撤单已生效
   ├── order_status = PAID → 撤单未生效，订单仍为已支付（可重新发起撤单或退款）
   └── 其他状态 → 继续轮询查询
4. 若查询仍无法确认，建议人工介入处理
```

## 核心流程

```
1. 收银系统组装请求参数（terminal_sn, sn 或 client_sn）
2. 计算签名（参考 shared-reference/SqbSignUtil），POST 到 /upay/v2/cancel
3. 解析响应：
   └─ result_code（通信层）
       └─ biz_response.result_code（业务层）
4. 根据 result_code 判定撤单结果
5. 若为 CANCEL_ERROR 或 CANCEL_ABORT_ERROR，调用查询接口确认
```

## 陷阱与注意事项

1. **所有交易都是真实的**（无沙盒环境）—— 撤单操作不可逆
2. **签名字符串一致性**—— MD5 计算时的 body 字符串必须与实际发送的完全一致
3. **当天限制**—— 跨天后无法撤单，只能走退款流程
4. **已部分退款不可撤单**—— 已发生过部分退款的订单，只能继续退款
5. **超时后必须查询确认**—— 网络超时不代表撤单失败，必须查询确认

## 架构设计

```
项目结构
├── controller/
│   └── SqbCancelController          # 撤单控制器
├── service/
│   ├── SqbCancelService             # 撤单核心逻辑
│   └── SqbQueryService              # 查询确认逻辑
├── model/
│   ├── CancelRequest                # 撤单请求 DTO
│   ├── CancelResponse               # 撤单响应 DTO
│   └── CancelResultCode             # 撤单结果码枚举
└── util/
    ├── SqbSignUtil                   # 签名工具类（shared-reference）
    └── SqbHttpClient                 # HTTP 客户端封装
```

## 生成规则

当生成撤单接口代码时，**必须**包含：
1. 签名逻辑引用 `shared-reference/SqbSignUtil`（MD5(body + terminal_key)）
2. 撤单结果判定逻辑（CANCEL_SUCCESS / CANCEL_ERROR / CANCEL_ABORT_SUCCESS / CANCEL_ABORT_ERROR）
3. 撤单失败后的查询确认流程（调用 sqb-query 确认订单最终状态）
4. 当天限制的提醒注释（仅限当日 00:00 后的交易）
5. 生成代码注释中标注 `⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易`

**可选但建议**包含：
- 撤单前的订单状态校验
- 已部分退款订单的拦截逻辑
- 超时处理
- 日志记录

## 代码示例

见 `reference/` 目录：
- `CancelExample.java` — Java 完整示例（OkHttp + Jackson）
- `cancel_example.py` — Python 完整示例（requests）
