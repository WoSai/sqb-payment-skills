# 收钱吧支付 Skills（shouqianba-payment-skills）

这个仓库用来给 AI 编码助手提供收钱吧支付接入知识。你可以把这里的 `SKILL.md` 提供给 Codex、Claude Code、Cursor 等工具，让 AI 按约定的分层方式生成收钱吧接入代码，而不是只生成零散示例。

首页重点放在怎么开始使用。分层原则、设计边界和迁移说明放在文末文档链接中。

这个项目的目标是帮助 AI 生成一套**供开发者参考正确接入收钱吧支付API的代码骨架（Adapter / Integration Layer）**。

- 从零生成收钱吧某个接口的接入骨架
- 在现有项目里补签名、状态判定、轮询、回调验签等模块
- 让 AI 生成更接近实际项目结构的 `protocol/client`、`adapter`、`support`、`bootstrap` 代码
- 为前端生成收银台 UI，并对接你自己的后端支付接口

适用场景包括：

- B 扫 C：付款码支付
- C 扫 B：预下单生成二维码
- 终端激活、签到、查询、退款、撤单、回调通知
- 已有项目做局部补齐

当前仓库提供 **Java / Python** 参考实现；其他语言可基于 `SKILL.md` 生成，但暂不提供官方参考代码。

## 快速上手

### 第一步：选择你要用的 skill

如果你要从零接入一个接口，优先选业务接口 skill：

- `sqb-activate`：终端激活
- `sqb-checkin`：终端签到 / 密钥轮换
- `sqb-pay`：付款码支付
- `sqb-precreate`：预下单
- `sqb-query`：订单查询
- `sqb-refund`：退款
- `sqb-cancel`：撤单
- `sqb-notify`：异步回调

如果你只缺某个通用模块，优先选共享 skill：

- `sqb-signing`：MD5 请求签名
- `sqb-status-parsing`：三层状态判定
- `sqb-polling`：参数化轮询
- `sqb-callback-verify`：RSA 回调验签

如果你要做前端收银界面，使用：

- `sqb-cashier-ui`：收银台 UI 与扫码交互

### 第二步：把 skill 提供给 AI 工具

#### Claude Code

```bash
cp -r sqb-api-skills/ ~/.claude/skills/
cp -r sqb-web-skills/ ~/.claude/skills/
```

#### Cursor

```bash
cp -r sqb-api-skills/ your-project/
cp -r sqb-web-skills/ your-project/
```

#### OpenClaw / Codex

把对应的 `SKILL.md` 文件加入上下文，或者放进 system prompt，让 AI 根据你的描述选择合适的 skill。

### 第三步：直接描述你的需求

这个仓库支持两种生成模式：

- 完整流程生成：适合从零接入一个接口
- 单独模块生成：适合在现有项目中补一个模块

一般来说：

- 你描述“接入支付、接入退款、接入回调”这一类需求时，会走完整流程生成
- 你描述“签名模块、轮询模块、回调验签”这一类需求时，会走单独模块生成

## 选型指引

### 什么时候用完整流程生成

适合这些情况：

- 你准备新接一个收钱吧接口
- 你希望 AI 按分层结构生成一套可落地骨架
- 你需要 `protocol/client`、`adapter`、`support`、`bootstrap` 一起产出

可以直接这样提：

- “帮我用 Java 接入收钱吧付款码支付”
- “帮我实现收钱吧预下单的完整分层接入”
- “帮我生成收钱吧退款适配层”

### 什么时候用单独模块生成

适合这些情况：

- 你项目已经接入了一部分，只缺某个模块
- 你只想补一个签名、轮询、状态判定或验签组件
- 你不希望 AI 再生成完整流程代码

可以直接这样提：

- “帮我实现收钱吧 MD5 签名模块”
- “帮我补一个 query adapter”
- “帮我生成回调验签层”
- “帮我生成退款金额校验逻辑”

## 使用示例

### 示例 1：从零接入付款码支付

把 `sqb-pay` 提供给 AI 后，可以直接提：

```text
帮我用 Java 接入收钱吧付款码支付，按 protocol/client、adapter、support、bootstrap 分层输出。
需要包含请求 DTO、签名调用、支付 adapter、状态判定、轮询策略和 facade 示例。
```

预期输出更接近下面这种结构，而不是只有一个 `PayExample`：

```text
shouqianba/
├── protocol/
│   ├── client/
│   ├── dto/
│   └── security/
├── adapter/
├── support/
└── bootstrap/
```

### 示例 2：只补签名模块

把 `sqb-signing` 提供给 AI 后，可以直接提：

```text
帮我生成一个可复用的收钱吧 MD5 签名模块，包含 serializeBody(body)、md5Sign(bodyStr, key)、buildAuthorization(sn, bodyStr, key)，并给出 Python 调用示例。
```

### 示例 3：生成回调处理骨架

把 `sqb-notify` 和 `sqb-callback-verify` 提供给 AI 后，可以直接提：

```text
帮我生成收钱吧异步回调处理代码，包含 HTTP POST 回调入口、RSA SHA256WithRSA 验签、幂等处理和 success 响应，按 bootstrap/controller、adapter、protocol/security 分层输出。
```

### 示例 4：生成前端收银台

把 `sqb-cashier-ui` 提供给 AI 后，可以直接提：

```text
帮我生成一个 Vue 收银台页面，支持金额输入、扫码枪输入、支付中/成功/失败/超时状态展示，并通过我自己的后端支付接口发起请求。
```

## 仓库结构

```text
shouqianba-payment-skills/
├── README.md
├── docs/
│   ├── architecture.md             # 分层架构说明
├── sqb-api-skills/
│   ├── README.md
│   ├── shared-reference/
│   ├── sqb-activate/
│   ├── sqb-checkin/
│   ├── sqb-pay/
│   ├── sqb-precreate/
│   ├── sqb-query/
│   ├── sqb-refund/
│   ├── sqb-cancel/
│   ├── sqb-notify/
│   ├── sqb-signing/
│   ├── sqb-status-parsing/
│   ├── sqb-polling/
│   └── sqb-callback-verify/
├── sqb-web-skills/
│   └── sqb-cashier-ui/
└── tests/
    └── validate_skills.py
```

你通常只需要关心这几部分：

- `sqb-api-skills/`：后端接口和通用模块 skill
- `sqb-web-skills/`：前端 UI skill
- `tests/`：结构和内容校验脚本

## 验证方式

运行仓库校验脚本，确认 skill 目录、文档、分层契约和参考代码都完整：

```bash
python3 tests/validate_skills.py
```

如果你想快速验证签名参考代码是否可执行，可以直接做语法校验：

```bash
python3 -m py_compile sqb-api-skills/sqb-signing/reference/sqb_sign_util.py
```

## 使用提醒

### 收钱吧没有沙盒环境

> 所有交易都是真实交易，会产生真实资金流动。测试完成后务必进行退款操作。

### 几个关键约束

- 激活接口使用 `vendor_sn / vendor_key`
- 交易接口使用 `terminal_sn / terminal_key`
- 交易结果要按 `result_code` → `biz_response.result_code` → `order_status` 三层判断
- 回调处理必须做 RSA 验签和幂等

## 设计摘要

这个项目的目标不是生成“企业支付平台”，而是帮助 AI 生成“收钱吧接入层”代码。推荐输出会围绕以下分层展开：

- `protocol/client`：HTTP 调用、签名、验签、DTO
- `adapter`：支付、预下单、查询、退款、撤单、回调适配器
- `support`：状态判定、轮询、幂等、密钥轮换
- `bootstrap`：配置、控制器、服务装配、示例入口

更详细的设计原则、边界说明和迁移背景，可以继续看这些文档：

- [分层架构说明](./docs/architecture.md)
- [API接口说明](https://doc.shouqianba.com)
- [收钱吧 API Skills 说明](./sqb-api-skills/README.md)
- [异常场景参考清单（P1）](./docs/error-scenarios.md)
- [terminal_key 轮换运行手册（P1）](./docs/key-rotation-runbook.md)
- [核心字段约束（P1）](./docs/field-constraints.md)
- [生成代码审查清单（P1）](./docs/generated-code-review-checklist.md)
- [English Onboarding Skeleton（P1）](./docs/en/README.md)
