---
name: sqb-precreate
description: "[后端项目使用]收钱吧C扫B预下单接口技能。用于生成二维码让顾客扫码支付。当用户提到收钱吧预下单、C扫B、二维码支付、QR支付、precreate时触发。"
version: "1.1"
tags: [payment, qrcode, c2b, precreate]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧C扫B预下单接口

## 引导词

### 完整流程
- 收钱吧预下单
- C扫B
- 二维码支付
- QR支付
- precreate
- 扫码付
- 顾客扫码
- 主扫支付

### 单独模块
- 预下单请求构建 / precreate request（→ 仅生成请求构建模块）
- 二维码处理 / QR code / qr_code 提取（→ 仅生成二维码处理模块）

## 概述

C扫B（预下单）是收钱吧的另一核心支付场景：商户系统向收钱吧发起预下单请求，获取二维码内容（`qr_code`），前端将其渲染为二维码，由顾客使用微信/支付宝扫码完成支付。支持微信支付和支付宝。

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
>
> 签名逻辑详见 `shared-reference/SqbSignUtil`。

## 接口说明

| 项目 | 说明 |
|---|---|
| 请求路径 | `/upay/v2/precreate` |
| 请求方法 | POST |
| Content-Type | `application/json; charset=utf-8` |
| API 域名 | `https://vsi-api.shouqianba.com` |

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| terminal_sn | string | Y | 终端序列号 |
| client_sn | string | Y | 商户系统订单号，**必须全局唯一** |
| total_amount | string | Y | 交易总金额，单位为**分** |
| payway | string | Y | 支付方式（1=支付宝, 3=微信）— **预下单时必填** |
| subject | string | Y | 交易简介 |
| operator | string | Y | 操作员 |
| description | string | N | 交易描述 |
| extended | object | N | 扩展参数 |
| reflect | string | N | 反射参数，任意字符串，原样返回 |
| notify_url | string | N | 回调通知地址 |

### payway 支付渠道

| payway | 渠道 |
|---|---|
| 1 | 支付宝 |
| 3 | 微信支付 |

> **重要**：与 B扫C 付款码支付不同，预下单接口中 `payway` 为**必填**参数。因为预下单需要指定支付渠道来生成对应的二维码。

## 请求示例

```json
{
    "terminal_sn": "10298371039",
    "client_sn": "20230615143052001",
    "total_amount": "100",
    "payway": "3",
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
| qr_code | **二维码内容字符串**（前端需渲染为二维码图片） |
| finish_time | 交易完成时间 |
| channel_finish_time | 渠道完成时间 |
| subject | 交易简介 |
| operator | 操作员 |

## 响应示例

```json
{
    "result_code": "200",
    "biz_response": {
        "result_code": "PRECREATE_SUCCESS",
        "data": {
            "sn": "7892840250140846",
            "client_sn": "20230615143052001",
            "status": "IN_QUEUE",
            "order_status": "IN_QUEUE",
            "total_amount": "100",
            "qr_code": "https://qr.alipay.com/bax01234abcd5678efgh",
            "subject": "星巴克咖啡",
            "operator": "cashier_01"
        }
    }
}
```

## 核心流程

```
1. 收银系统组装请求参数（client_sn, total_amount, payway, subject, operator）
2. 校验 payway 必填
3. 计算签名，POST 到 /upay/v2/precreate
4. 解析三层响应：
   └─ result_code（通信层）
       └─ biz_response.result_code（业务层）
           └─ order_status（订单状态）
5. 从 biz_response.data 中提取 qr_code 字段
6. 前端将 qr_code 渲染为二维码图片供顾客扫码
7. 启动轮询查询，等待顾客完成支付
```

## 交易结果判定（关键）

> 三层状态判定逻辑详见 `shared-reference/SqbStatusUtil`。

### 第一层：result_code（通信层）

| result_code | 含义 | 处理 |
|---|---|---|
| `200` | 通信成功 | 继续判断 biz_response |
| 非 `200` | 通信失败 | 根据错误码处理，可能需要重试 |

### 第二层：biz_response.result_code（业务层）

| result_code | 含义 | 处理 |
|---|---|---|
| `PRECREATE_SUCCESS` | 预下单成功 | 提取 qr_code，展示二维码，启动轮询 |
| `PRECREATE_FAIL` | 预下单失败 | 交易结束 |
| `PRECREATE_IN_PROGRESS` | 预下单处理中 | 启动查询轮询 |
| `PRECREATE_FAIL_ERROR` | 预下单失败（不确定） | 启动查询轮询 |

### 第三层：order_status（订单最终状态）

| order_status | 类型 | 处理方式 |
|---|---|---|
| `PAID` | **最终状态** | 支付成功，展示成功页面 |
| `PAY_CANCELED` | **最终状态** | 支付失败/已撤销，可重新收款 |
| `IN_QUEUE` | 非最终状态 | 预下单已创建，等待顾客扫码，**必须轮询** |
| `CREATED` | 非最终状态 | 订单已创建但未完成，**必须轮询** |
| `PAY_ERROR` | 非最终状态 | 状态未知，**必须轮询或人工确认** |

> **重要**：只有 `PAID` 和 `PAY_CANCELED` 是最终状态。收到其他状态时，**禁止**直接判定为成功或失败，必须启动轮询查询。

## 轮询策略

当 order_status 为非最终状态时，必须启动自动轮询（调用 sqb-query）：

```
时间段          间隔       说明
0 ~ 30秒       2秒       高频轮询，快速获取结果
30秒 ~ 超时    5秒       降低频率，等待顾客扫码
```

- 预下单订单约 **4 分钟（240 秒）** 后自动过期
- 轮询直到获得最终状态（PAID 或 PAY_CANCELED）或订单过期
- 轮询策略配置引用 `shared-reference/SqbPollingUtil` 的 `PRECREATE_POLLING_CONFIG`

> 与 B扫C 的轮询策略不同：预下单因为需要等待顾客扫码，初始轮询更频繁（2秒），但总超时更长（240秒）。

## QR Code 展示

预下单成功后，`biz_response.data.qr_code` 返回的是二维码内容字符串，**前端需要将其渲染为二维码图片**供顾客扫码：

- Web 端可使用 `qrcode.js`、`vue-qrcode`、`react-qrcode` 等库
- 移动端可使用 `ZXing`（Java/Kotlin）、`CoreImage`（iOS）等库
- 二维码图片建议尺寸不小于 200x200 像素
- 建议在二维码下方显示金额信息和倒计时

## 关键参数说明

### payway（支付方式）
- **预下单时为必填参数**（与 B扫C 不同）
- `1` = 支付宝，`3` = 微信支付
- 决定生成哪种支付渠道的二维码

### client_sn（商户订单号）
- **必须全局唯一**，建议格式：`日期 + 门店编号 + 流水号`
- 重复的 client_sn 会被拒绝
- 用于后续查询和退款的关键标识

### total_amount（金额）
- 单位为**分**（1元 = 100分）
- 字符串类型
- 不支持小数

### subject（交易简介）
- 会显示在顾客的支付宝/微信账单中
- 建议填写门店名称 + 商品摘要

## 陷阱与注意事项

1. **所有交易都是真实的**（无沙盒环境）—— 测试后务必退款
2. **payway 必填**—— 预下单必须指定支付渠道，不像 B扫C 可以自动识别
3. **签名字符串一致性**—— MD5 计算时的 body 字符串必须与实际发送的完全一致
4. **金额单位为分**—— 100 表示 1 元，不要传入 "1.00"
5. **X-Forwarded-For**—— 建议在请求头中传入终端的真实公网 IP
6. **client_sn 不可复用**—— 支付失败后不能用相同 client_sn 重试，必须生成新的 client_sn
7. **二维码有效期**—— 预下单二维码约 4 分钟后过期，过期后需重新发起预下单
8. **qr_code 需要渲染**—— 接口返回的是字符串，不是图片，前端必须用二维码库渲染

## 架构设计

```
项目结构
├── controller/
│   └── SqbPrecreateController       # 预下单控制器
├── service/
│   ├── SqbPrecreateService          # 预下单核心逻辑
│   └── SqbQueryService              # 查询轮询逻辑
├── model/
│   ├── PrecreateRequest             # 预下单请求 DTO
│   ├── PrecreateResponse            # 预下单响应 DTO
│   └── OrderStatus                  # 订单状态枚举
└── util/
    ├── SqbSignUtil                  # 签名工具类
    └── SqbHttpClient                # HTTP 客户端封装
```

## 实现步骤

1. 创建/复用签名工具类 `SqbSignUtil`（引用 `shared-reference/SqbSignUtil`）
2. 创建预下单请求 DTO（terminal_sn, client_sn, total_amount, payway, subject, operator）
3. 添加 payway 必填校验
4. 实现预下单服务，包含签名计算和 HTTP 调用
5. 实现三层状态判定逻辑（引用 `shared-reference/SqbStatusUtil`）
6. 提取 qr_code 字段并返回给前端
7. 实现轮询查询机制（引用 `shared-reference/SqbPollingUtil` 的 `PRECREATE_POLLING_CONFIG`）
8. 创建控制器接口供收银台调用
9. 添加 client_sn 唯一性生成逻辑

## 生成规则

当生成预下单支付代码时，**必须**包含：
1. 签名逻辑引用 `shared-reference/SqbSignUtil`（MD5(body + terminal_key)，Authorization 头格式：terminal_sn + 空格 + sign）
2. 三层状态判定引用 `shared-reference/SqbStatusUtil`
3. 轮询引用 `shared-reference/SqbPollingUtil`（使用 `PRECREATE_POLLING_CONFIG`：前30秒每2秒，之后每5秒，总超时240秒）
4. QR code 生成提示（前端需要将 `qr_code` 字段渲染为二维码图片）
5. payway 必填校验（预下单时 payway 为必填参数）
6. 生成代码注释中标注 `⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易`

**可选但建议**包含：
- 二维码过期倒计时提示
- 超时处理
- 日志记录
- 异常重试

## 模块化生成

本技能支持单独生成以下模块。当用户 prompt 中包含模块关键词时，仅生成对应模块代码，不生成完整流程。

> 签名、三层状态判定、轮询框架等跨接口共享模块请使用对应的独立 Skill（sqb-signing、sqb-status-parsing、sqb-polling）。

### 模块：预下单请求构建

**触发关键词**："预下单请求"、"precreate request"、"C 扫 B 请求"

**生成规则**：
1. 构建 JSON 请求体，包含 terminal_sn、client_sn、total_amount、payway、subject、operator
2. **payway 为必填参数**（不同于 pay 接口）：1=支付宝, 3=微信, 4=百度, 5=京东
3. 调用签名工具计算 Authorization 头
4. POST 请求到 `/upay/v2/precreate`
5. 返回响应中的 qr_code 字段

**参考代码（Java）**：
```java
// 预下单请求（payway 为必填参数）
ObjectNode body = mapper.createObjectNode();
body.put("terminal_sn", terminalSn);
body.put("client_sn", clientSn);
body.put("total_amount", totalAmount);    // 单位：分
body.put("payway", payway);              // 必填：1=支付宝, 3=微信
body.put("subject", subject);
body.put("operator", operator);

String bodyStr = mapper.writeValueAsString(body);
String sign = SqbSignUtil.md5Sign(bodyStr, terminalKey);
// POST to https://vsi-api.shouqianba.com/upay/v2/precreate
```

**参考代码（Python）**：
```python
# 预下单请求（payway 为必填参数）
body = {
    "terminal_sn": terminal_sn,
    "client_sn": client_sn,
    "total_amount": total_amount,    # 单位：分
    "payway": payway,                # 必填：1=支付宝, 3=微信
    "subject": subject,
    "operator": operator,
}
body_str = json.dumps(body, ensure_ascii=False)
sign = md5_sign(body_str, terminal_key)
# POST to https://vsi-api.shouqianba.com/upay/v2/precreate
```

### 模块：二维码处理

**触发关键词**："二维码提取"、"QR code"、"qr_code 渲染"、"生成二维码"

**生成规则**：
1. 从预下单响应的 `biz_response.data.qr_code` 字段提取二维码内容
2. 使用 QR 库生成二维码图片或渲染到页面
3. 注释提醒二维码有效期（通常几分钟），过期需重新预下单

**参考代码（Java）**：
```java
// 从预下单响应提取二维码
JsonNode data = response.path("biz_response").path("data");
String qrCode = data.path("qr_code").asText();
// 使用 ZXing 等库生成二维码图片
// BitMatrix matrix = new QRCodeWriter().encode(qrCode, BarcodeFormat.QR_CODE, 300, 300);
System.out.println("二维码内容: " + qrCode);
// ⚠️ 二维码有有效期，过期需重新调用预下单接口
```

**参考代码（Python）**：
```python
# 从预下单响应提取二维码
qr_code = response["biz_response"]["data"]["qr_code"]
# 使用 qrcode 库生成二维码图片
# import qrcode
# img = qrcode.make(qr_code)
# img.save("payment_qr.png")
print(f"二维码内容: {qr_code}")
# ⚠️ 二维码有有效期，过期需重新调用预下单接口
```

## 代码示例

见 `reference/` 目录：
- `PrecreateExample.java` — Java 完整示例（含轮询，OkHttp + Jackson）
- `precreate_example.py` — Python 完整示例（含轮询，requests）
