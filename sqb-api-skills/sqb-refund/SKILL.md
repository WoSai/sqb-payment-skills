---
name: sqb-refund
description: "[后端项目使用]收钱吧退款接口技能。用于对已支付订单进行全额或部分退款。当用户提到收钱吧退款、订单退款、refund、退钱、/refund时触发。"
version: "1.1"
tags: [payment, refund, partial-refund]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧退款接口

## 引导词

### 完整流程
- 收钱吧退款
- 订单退款
- refund
- 退钱
- /refund
- 部分退款
- 全额退款
- /upay/v2/refund
- partial refund
- 退款接口

### 单独模块
- 退款请求构建 / refund request（→ 仅生成退款请求模块）
- 退款金额校验 / 累计退款 / 部分退款校验（→ 仅生成退款校验模块）
- 退款号生成 / refund_request_no（→ 仅生成退款号模块）

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

## 部分退款（关键场景）

### 基本规则

- 退款金额可小于原订单金额，实现部分退款
- 多次部分退款的累计金额不能超过原订单金额
- 部分退款后 order_status 变为 `PARTIAL_REFUNDED`
- 全额退款后 order_status 变为 `REFUNDED`
- 退款无次数限制，直到可退金额为 0

### 部分退款安全流程

```
1. 查询原始订单（sqb-query），获取 total_amount 和 net_amount
2. 计算可退余额：refundable = net_amount（net_amount = total_amount - 已退款金额）
3. 校验本次退款金额 ≤ refundable，否则拒绝
4. 生成唯一 refund_request_no（建议格式：REF + 日期 + 原订单号 + 序号）
5. 发起退款请求
6. 退款结果判定（REFUND_SUCCESS / REFUND_IN_PROGRESS / REFUND_FAIL）
7. 若为 REFUND_IN_PROGRESS，轮询查询确认最终退款状态
8. 退款成功后再次查询订单，确认 order_status 和 net_amount 更新正确
```

### 退款状态机

```
PAID → (部分退款) → PARTIAL_REFUNDED → (继续退款) → PARTIAL_REFUNDED → (退完) → REFUNDED
```

### refund_request_no 唯一性管理

多次部分退款时，每次必须使用不同的 `refund_request_no`。建议格式：

```
REF{原订单号}_{序号}
例如：REF20230615143052001_01, REF20230615143052001_02
```

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

当生成退款接口代码时，**必须**包含：
1. 签名逻辑引用 `shared-reference/SqbSignUtil`，不要自行编写签名实现
2. refund_request_no 唯一性生成逻辑
3. **部分退款时的累计金额校验**（先查询 net_amount，计算可退余额，累计退款不超过原始金额）
4. 退款结果判定（含异步轮询确认 REFUND_SUCCESS）
5. 退款失败的错误处理
6. **在类/模块级别注释中标注**：`⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实退款`
7. **测试用例模板中默认包含退款清理说明**

## 模块化生成

本技能支持单独生成以下模块。当用户 prompt 中包含模块关键词时，仅生成对应模块代码，不生成完整流程。

> 签名等跨接口共享模块请使用对应的独立 Skill（sqb-signing）。

### 模块：退款请求构建

**触发关键词**："退款请求"、"refund request"、"发起退款"

**生成规则**：
1. 构建 JSON 请求体，包含 sn（或 client_sn）、refund_request_no、refund_amount、operator
2. sn 和 client_sn 二选一，sn 优先
3. 签名并 POST 到 `/upay/v2/refund`
4. 支持全额退款和部分退款
5. ⚠️ 金额单位为分

**参考代码（Java）**：
```java
// 退款请求构建
ObjectNode body = mapper.createObjectNode();
body.put("sn", orderSn);                            // 收钱吧订单号（与 client_sn 二选一）
body.put("refund_request_no", refundRequestNo);      // 退款请求号（必须唯一）
body.put("refund_amount", refundAmount);             // 退款金额（单位：分）
body.put("operator", operator);

String bodyStr = mapper.writeValueAsString(body);
String sign = SqbSignUtil.md5Sign(bodyStr, terminalKey);
// POST to https://vsi-api.shouqianba.com/upay/v2/refund
```

**参考代码（Python）**：
```python
# 退款请求构建
body = {
    "sn": order_sn,                              # 收钱吧订单号（与 client_sn 二选一）
    "refund_request_no": refund_request_no,       # 退款请求号（必须唯一）
    "refund_amount": refund_amount,               # 退款金额（单位：分）
    "operator": operator,
}
body_str = json.dumps(body, ensure_ascii=False)
sign = md5_sign(body_str, terminal_key)
# POST to https://vsi-api.shouqianba.com/upay/v2/refund
```

### 模块：退款金额校验

**触发关键词**："退款校验"、"累计退款"、"部分退款校验"、"net_amount 校验"

**生成规则**：
1. 查询原始订单获取 net_amount（实收金额，扣除手续费后的金额）
2. 累计已退款金额 + 本次退款金额 ≤ net_amount
3. 部分退款场景需记录历史退款记录
4. 金额单位为分，使用整数计算避免浮点精度问题

**参考代码（Java）**：
```java
/**
 * 退款金额校验：确保累计退款不超过实收金额
 *
 * @param netAmount         原始订单实收金额（分）
 * @param alreadyRefunded   已退款累计金额（分）
 * @param thisRefundAmount  本次退款金额（分）
 */
public boolean validateRefundAmount(long netAmount, long alreadyRefunded, long thisRefundAmount) {
    if (thisRefundAmount <= 0) {
        throw new IllegalArgumentException("退款金额必须大于 0");
    }
    if (alreadyRefunded + thisRefundAmount > netAmount) {
        throw new IllegalArgumentException(
            String.format("累计退款金额(%d + %d = %d分)超过实收金额(%d分)",
                alreadyRefunded, thisRefundAmount, alreadyRefunded + thisRefundAmount, netAmount));
    }
    return true;
}
```

**参考代码（Python）**：
```python
def validate_refund_amount(net_amount: int, already_refunded: int, this_refund: int) -> bool:
    """退款金额校验：确保累计退款不超过实收金额（单位：分）"""
    if this_refund <= 0:
        raise ValueError("退款金额必须大于 0")
    if already_refunded + this_refund > net_amount:
        raise ValueError(
            f"累计退款金额({already_refunded} + {this_refund} = {already_refunded + this_refund}分)"
            f"超过实收金额({net_amount}分)")
    return True
```

### 模块：退款号生成

**触发关键词**："refund_request_no"、"退款单号"、"退款请求号"

**生成规则**：
1. 格式：REF + 时间戳 + UUID 前缀，全局唯一
2. 同一笔退款重试时使用**相同**的 refund_request_no（幂等性）
3. 不同退款请求使用不同的 refund_request_no

**参考代码（Java）**：
```java
private String generateRefundRequestNo() {
    return "REF" + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmssSSS"))
        + UUID.randomUUID().toString().substring(0, 4);
}
```

**参考代码（Python）**：
```python
import uuid
from datetime import datetime

def generate_refund_request_no() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]
    return f"REF{timestamp}{uuid.uuid4().hex[:4]}"
```

## 代码示例

见 `reference/` 目录：
- `RefundExample.java` — Java 示例（OkHttp + Jackson）
- `refund_example.py` — Python 示例（requests）
