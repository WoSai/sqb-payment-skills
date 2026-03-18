---
name: sqb-pay
description: 收钱吧B扫C付款码支付接口。触发词：收钱吧支付、付款码支付、扫码收款、B扫C、shouqianba pay、/pay
---

# 收钱吧付款码支付接口

## 概述

B扫C（付款码支付）是收钱吧核心支付场景：商户使用扫码枪/摄像头扫描顾客手机上的付款码，完成扣款。支持微信支付、支付宝、云闪付等主流支付渠道。

## 前置条件

- 已完成终端激活（sqb-activate），持有 `terminal_sn` 和 `terminal_key`
- 建议当日已完成签到（sqb-checkin）
- API 域名：`https://vsi-api.shouqianba.com`
- 协议：HTTPS POST，Content-Type: `application/json; charset=utf-8`

## 签名方式

```
Authorization: {terminal_sn} {MD5(request_body + terminal_key)}
```

> 注意：sn 和 sign 之间有且仅有一个空格。request_body 必须是 UTF-8 编码的原始 JSON 字符串，签名时的字符串必须和实际请求体完全一致（包括字段顺序、空格等）。

## 接口信息

- **URL**: `/api/v2/pay`
- **方法**: POST

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| terminal_sn | string | Y | 终端序列号 |
| client_sn | string | Y | 商户系统订单号，**必须全局唯一** |
| total_amount | string | Y | 交易总金额，单位为**分** |
| dynamic_id | string | Y | 顾客付款码内容（扫码枪扫描获得） |
| subject | string | Y | 交易简介，**显示在顾客支付宝/微信账单中** |
| operator | string | Y | 操作员，门店对账时使用 |
| description | string | N | 交易描述 |
| longitude | string | N | 经度 |
| latitude | string | N | 纬度 |
| extended | object | N | 扩展参数 |
| reflect | string | N | 反射参数，任意字符串，原样返回 |
| notify_url | string | N | 回调通知地址 |

## 请求示例

```json
{
    "terminal_sn": "10298371039",
    "client_sn": "20230615143052001",
    "total_amount": "100",
    "dynamic_id": "130818341921600584",
    "subject": "星巴克咖啡",
    "operator": "cashier_01"
}
```

## 响应参数

| 参数 | 说明 |
|---|---|
| sn | 收钱吧订单号 |
| client_sn | 商户订单号 |
| trade_no | 支付渠道交易号（支付宝/微信） |
| status | 订单状态（见下方状态表） |
| order_status | 同 status |
| total_amount | 交易总金额（分） |
| net_amount | 实收金额（分） |
| finish_time | 交易完成时间 |
| channel_finish_time | 渠道完成时间 |
| subject | 交易简介 |
| operator | 操作员 |

## 响应示例

```json
{
    "result_code": "200",
    "biz_response": {
        "result_code": "PAY_SUCCESS",
        "data": {
            "sn": "7892840250140845",
            "client_sn": "20230615143052001",
            "trade_no": "2023061522001456781234567890",
            "status": "PAID",
            "order_status": "PAID",
            "total_amount": "100",
            "net_amount": "97",
            "finish_time": "1686816652000",
            "channel_finish_time": "1686816651000",
            "subject": "星巴克咖啡",
            "operator": "cashier_01"
        }
    }
}
```

## 核心流程

```
1. 收银系统组装请求参数（client_sn, total_amount, dynamic_id, subject, operator）
2. 计算签名，POST 到 /api/v2/pay
3. 解析三层响应：
   └─ result_code（通信层）
       └─ biz_response.result_code（业务层）
           └─ order_status（订单状态）
4. 根据 order_status 判定交易结果
5. 若为非最终状态，启动轮询查询（见 sqb-query skill）
```

## 交易结果判定（关键）

### 第一层：result_code（通信层）

| result_code | 含义 | 处理 |
|---|---|---|
| `200` | 通信成功 | 继续判断 biz_response |
| 非 `200` | 通信失败 | 根据错误码处理，可能需要重试 |

### 第二层：biz_response.result_code（业务层）

| result_code | 含义 | 处理 |
|---|---|---|
| `PAY_SUCCESS` | 支付成功 | 检查 order_status |
| `PAY_FAIL` | 支付失败 | 交易结束 |
| `PAY_FAIL_ERROR` | 支付失败（不确定） | 启动查询轮询 |
| `PAY_IN_PROGRESS` | 支付处理中 | 启动查询轮询 |

### 第三层：order_status（订单最终状态）

| order_status | 类型 | 处理方式 |
|---|---|---|
| `PAID` | **最终状态** | 支付成功，展示成功页面 |
| `PAY_CANCELED` | **最终状态** | 支付失败/已撤销，可重新收款 |
| `CREATED` | 非最终状态 | 订单已创建但未完成，**必须轮询** |
| `PAY_ERROR` | 非最终状态 | 状态未知，**必须轮询或人工确认** |

> **重要**：只有 `PAID` 和 `PAY_CANCELED` 是最终状态。收到其他状态时，**禁止**直接判定为成功或失败，必须启动轮询查询。

## 轮询策略

当 order_status 为非最终状态时，必须启动自动轮询（调用 sqb-query）：

```
时间段          间隔       说明
0 ~ 60秒       3秒       高频轮询，快速获取结果
60秒 ~ 超时    10秒      降低频率，等待用户操作
```

- 前台可在 60 秒左右弹出超时提示，询问用户是否继续等待
- 轮询直到获得最终状态（PAID 或 PAY_CANCELED）或人工介入

## 有密支付场景

部分交易需要用户在手机上输入密码（如大额交易）：
1. 收钱吧返回 `PAY_IN_PROGRESS` 状态
2. 收银台应提示"等待顾客输入密码"
3. 持续轮询等待最终结果
4. 超时后提示收银员确认

## 关键参数说明

### client_sn（商户订单号）
- **必须全局唯一**，建议格式：`日期 + 门店编号 + 流水号`
- 重复的 client_sn 会被拒绝
- 用于后续查询和退款的关键标识

### dynamic_id（付款码）
- 扫码枪扫描顾客手机付款码获得的字符串
- 不同支付渠道（微信/支付宝/云闪付）的付款码格式不同
- 收钱吧会自动识别支付渠道，开发者无需判断

### total_amount（金额）
- 单位为**分**（1元 = 100分）
- 字符串类型
- 不支持小数

### subject（交易简介）
- 会显示在顾客的支付宝/微信账单中
- 建议填写门店名称 + 商品摘要

## 陷阱与注意事项

1. **所有交易都是真实的**（无沙盒环境）—— 测试后务必退款
2. **签名字符串一致性**—— MD5 计算时的 body 字符串必须与实际发送的完全一致
3. **金额单位为分**—— 100 表示 1 元，不要传入 "1.00"
4. **X-Forwarded-For**—— 建议在请求头中传入终端的真实公网 IP
5. **幂等性**—— 相同 client_sn 重复请求会返回已有订单信息，不会重复扣款
6. **付款码有效期**—— 付款码通常有效期为 1 分钟，超时需让顾客刷新

## 生成规则

当生成付款码支付代码时，**必须**包含：
1. 正确的签名计算逻辑（MD5(body + terminal_key)）
2. Authorization 头的正确格式（terminal_sn + 空格 + sign）
3. 三层响应状态判定逻辑
4. 非最终状态下的自动轮询机制
5. client_sn 全局唯一性保证
6. 金额单位为分的提醒注释

**可选但建议**包含：
- 有密支付的等待提示
- 超时处理
- 日志记录
- 异常重试

## 参考代码

见 `reference/` 目录下的多语言示例。
