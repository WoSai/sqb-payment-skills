# 收钱吧支付 Skills（shouqianba-payment-skills）

> 将收钱吧支付 API 对接知识封装为 AI Agent 可消费的 SKILL.md 格式，让 Claude Code / Cursor / Codex 等 AI 编码助手通过自然语言指令自动生成符合规范的对接代码。

## 适用场景

B扫C（付款码支付）：商户扫描顾客手机上的付款码完成收款。

## 技能包结构

```
shouqianba-payment-skills/
├── README.md                          # 本文件
├── sqb-api-skills/                    # 后端技能包
│   ├── README.md
│   ├── sqb-activate/                  # 激活接口
│   │   ├── SKILL.md
│   │   └── reference/
│   ├── sqb-checkin/                   # 签到接口
│   │   ├── SKILL.md
│   │   └── reference/
│   ├── sqb-pay/                       # 付款码支付（核心）
│   │   ├── SKILL.md
│   │   └── reference/
│   ├── sqb-query/                     # 查询接口
│   │   ├── SKILL.md
│   │   └── reference/
│   ├── sqb-refund/                    # 退款接口
│   │   ├── SKILL.md
│   │   └── reference/
│   └── sqb-notify/                    # 回调处理
│       ├── SKILL.md
│       └── reference/
└── sqb-web-skills/                    # 前端技能包
    └── sqb-cashier-ui/               # 收银台 UI 组件
        ├── SKILL.md
        └── reference/
```

## 快速开始

### 1. 在 Claude Code 中使用

将本仓库克隆到项目目录，或将 `sqb-api-skills` 添加为项目的子目录：

```bash
git clone https://github.com/anthropics/sqb-payment-skills.git
```

然后在 Claude Code 中直接输入自然语言指令，例如：

- "帮我用 Java 接入收钱吧付款码支付"
- "生成收钱吧退款接口的 Python 代码"
- "帮我实现收钱吧终端激活流程"

### 2. 在 Cursor 中使用

将 SKILL.md 文件添加到 Cursor 的上下文中，AI 将自动识别并生成对接代码。

## 核心概念

### 终端体系

收钱吧采用 **服务商(vendor) → 商户(merchant) → 门店(store) → 终端(terminal)** 的四级体系：

- **vendor_sn / vendor_key**：服务商凭证，用于激活接口签名
- **terminal_sn / terminal_key**：终端凭证，用于交易接口签名（激活后获得）

### 签名机制

所有交易接口使用统一的签名方式：

```
Authorization: {terminal_sn} {MD5(request_body + terminal_key)}
```

### 交易结果判定

三层状态判定：`result_code` → `biz_response.result_code` → `order_status`

| order_status | 类型 | 处理方式 |
|---|---|---|
| `PAID` | 最终状态 | 支付成功 |
| `PAY_CANCELED` | 最终状态 | 支付失败 |
| `REFUNDED` | 最终状态 | 已全额退款 |
| `PARTIAL_REFUNDED` | 最终状态 | 已部分退款 |
| `CREATED` | 非最终状态 | 支付中，需轮询 |
| `PAY_ERROR` | 非最终状态 | 状态未知，需轮询 |

### 轮询策略

- 0~60 秒：每 3 秒查询一次
- 60 秒后：每 10 秒查询一次
- 建议前台在适当时间弹出超时提示

## 重要提醒

> **收钱吧没有沙盒环境。所有交易（包括使用测试激活码产生的交易）都是真实交易，会产生真实资金流动。测试完成后务必进行退款操作。**

## 接口调用顺序

```
激活(activate) → 签到(checkin) → 付款(pay) → 查询(query) → 退款(refund)
```

1. **激活**（一次性）：使用激活码获取 terminal_sn 和 terminal_key
2. **签到**（每天）：更新 terminal_key，保持终端活跃
3. **付款 / 查询 / 退款**：日常交易操作

## 技能优先级

| 优先级 | 技能 | 说明 |
|---|---|---|
| P0 | sqb-pay, sqb-query, sqb-refund | 完整收款-查询-退款闭环 |
| P1 | sqb-activate, sqb-checkin | 终端激活与签到，交易前提 |
| P2 | sqb-notify | 异步回调通知处理 |
| P3 | sqb-cashier-ui | 前端收银界面参考 |

## API 域名

| 环境 | 域名 |
|---|---|
| 生产环境 | `https://vsi-api.shouqianba.com` |

## 参考资源

- [收钱吧开发者文档](https://doc.shouqianba.com/)
- [收钱吧 GitHub (WoSai)](https://github.com/WoSai)
- [Java Demo](https://github.com/WoSai/Shouqianba-mobile-payment-API-demo-Java)
- [Python Demo](https://github.com/WoSai/Shouqianba-mobile-payment-API-demo-Python)
- [C# Demo](https://github.com/WoSai/Shouqianba-mobile-payment-API-demo-CSharp)
- [API 文档源码](https://github.com/WoSai/shouqianba-doc)
