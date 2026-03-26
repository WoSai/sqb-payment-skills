# 收钱吧支付 Skills（shouqianba-payment-skills）

> 将收钱吧支付 API 对接知识封装为 AI Agent 可消费的 `SKILL.md` 格式，让 Claude Code / Cursor / OpenClaw / Codex 等 AI 编码助手通过自然语言指令，生成符合规范的收钱吧适配层代码。

## 项目定位

这个项目的目标不再只是“生成示例代码”，而是帮助 AI 生成一套**可落地的渠道适配层（Adapter / Integration Layer）**。

它的生成边界明确止步于：

- `protocol/client`：HTTP 调用、签名、验签、DTO
- `adapter`：支付、预下单、查询、退款、撤单、回调适配器
- `support`：状态映射、轮询、幂等、密钥轮换辅助
- `bootstrap`：框架对接骨架（配置、控制器、服务装配、示例入口）

它**不会**试图自动生成以下内容：

- 公司统一支付平台
- 多支付渠道路由与编排
- 风控、账务、清结算、对账平台
- 内部监控、权限、审计、工单体系

换句话说，本项目负责生成“收钱吧接入正确性”，而不是“企业支付平台完整性”。

## 适用场景

- **B扫C（付款码支付）**：商户扫描顾客手机上的付款码完成收款
- **C扫B（预下单）**：商户生成二维码，顾客扫码支付
- **已有项目局部补齐**：只补签名、状态判定、轮询、回调验签等模块
- **AI 辅助接入**：让 AI 生成符合统一分层规范的接入骨架，而不是散乱示例

## 分层设计

完整流程生成时，推荐输出如下目录结构：

```text
shouqianba/
├── protocol/
│   ├── client/                      # HTTP client、请求执行器
│   ├── dto/                         # request / response DTO
│   └── security/                    # 请求签名、回调验签
├── adapter/
│   ├── payment/                     # sqb-pay / sqb-precreate
│   ├── query/                       # sqb-query
│   ├── refund/                      # sqb-refund
│   ├── cancel/                      # sqb-cancel
│   └── terminal/                    # sqb-activate / sqb-checkin / sqb-notify
├── support/
│   ├── status/                      # 三层状态解析、状态映射
│   ├── polling/                     # 参数化轮询
│   ├── idempotency/                 # 回调去重、订单幂等辅助
│   └── key_rotation/                # terminal_key 更新与容灾
└── bootstrap/
    ├── config/                      # 配置与凭证注入
    ├── controller/                  # 回调入口 / 示例接口
    └── facade/                      # 对业务暴露的接入门面
```

## 两种生成模式

本技能包继续支持两种模式，且两种模式都以“分层设计”为基础。

### 模式一：完整流程生成（默认）

当你需要从零接入某个接口时，AI 生成该接口的一套**分层接入骨架**，而不是只有一个示例类。

输出通常包括：

- `protocol` 层中的请求 DTO、响应 DTO、签名 / 验签能力
- `adapter` 层中的渠道适配器
- `support` 层中的状态判定 / 轮询 / 幂等辅助
- `bootstrap` 层中的配置、示例服务或控制器骨架

示例：

- “帮我用 Java 接入收钱吧付款码支付”
- “帮我实现收钱吧预下单的完整分层接入”
- “帮我生成收钱吧退款适配层”

### 模式二：单独模块生成

当你已有项目，只缺某一层或某个模块时，AI 只生成对应模块。

示例：

- “帮我实现收钱吧 MD5 签名模块”
- “帮我补一个 query adapter”
- “帮我生成回调验签层”
- “帮我生成退款金额校验逻辑”

> 模式由 AI 根据 prompt 自动判断。命中模块关键词时进入单独模块模式，否则默认生成完整流程骨架。

## 技能包结构

```text
shouqianba-payment-skills/
├── README.md
├── docs/
│   ├── architecture.md             # 分层架构说明
│   └── migration.md                # 从旧版示例式技能迁移到新版分层技能
├── sqb-api-skills/
│   ├── README.md
│   ├── shared-reference/           # 共享参考代码（签名 / 状态 / 轮询）
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

## 技能分类

### 业务接口技能

- `sqb-activate`：终端激活
- `sqb-checkin`：终端签到 / 密钥轮换
- `sqb-pay`：B扫C 支付
- `sqb-precreate`：C扫B 预下单
- `sqb-query`：订单查询
- `sqb-refund`：退款（支持部分退款）
- `sqb-cancel`：撤单 / 冲正
- `sqb-notify`：异步回调通知

### 跨接口共享模块技能

- `sqb-signing`：MD5 请求签名
- `sqb-status-parsing`：三层状态判定
- `sqb-polling`：参数化轮询框架
- `sqb-callback-verify`：RSA 回调验签

### 前端技能

- `sqb-cashier-ui`：收银台 UI 与扫码交互示例

## 生成边界

### 应该生成

- 面向收钱吧的 provider adapter
- vendor / terminal 凭证签名逻辑
- 回调验签逻辑
- 三层状态判定和映射
- 查询轮询策略
- 退款、撤单、回调的安全边界代码
- 与 Spring / FastAPI / Flask / NestJS 等框架衔接的骨架

### 不应该生成

- 你们公司的统一 `PaymentGateway`
- 风控、账务、对账、营销编排
- 内部审计平台与告警平台
- 多渠道通用网关的最终抽象

## 安装指引

### Claude Code

```bash
cp -r sqb-api-skills/ ~/.claude/skills/
cp -r sqb-web-skills/ ~/.claude/skills/
```

### Cursor

```bash
cp -r sqb-api-skills/ your-project/
cp -r sqb-web-skills/ your-project/
```

### OpenClaw / Codex

将各 `SKILL.md` 文件加入上下文或 system prompt，让 AI 自动根据关键词匹配 skill。

## 核心概念

### 终端体系

收钱吧采用 **服务商(vendor) → 商户(merchant) → 门店(store) → 终端(terminal)** 的四级体系：

- `vendor_sn / vendor_key`：服务商凭证，用于激活接口签名
- `terminal_sn / terminal_key`：终端凭证，用于交易接口签名（激活后获得）

### 请求签名

所有交易接口统一使用：

```text
Authorization: {terminal_sn} {MD5(request_body + terminal_key)}
```

激活接口例外，使用：

```text
Authorization: {vendor_sn} {MD5(request_body + vendor_key)}
```

### 三层状态判定

交易结果必须按以下顺序判断：

1. `result_code`
2. `biz_response.result_code`
3. `order_status`

只有最终状态才允许对业务作出确定性结论。

### 轮询策略

- `sqb-pay`：0~60 秒每 3 秒，之后每 10 秒，总超时 120 秒
- `sqb-precreate`：0~30 秒每 2 秒，之后每 5 秒，总超时 240 秒

## 安全提醒

> **⚠️ 收钱吧没有沙盒环境。所有交易都是真实交易，会产生真实资金流动。测试完成后务必进行退款操作。**

技能在生成代码时必须显式保留这一提醒，尤其是支付、退款、撤单、查询相关流程。

## 验证测试

运行项目验证脚本，确认 skill 结构、文档、分层契约和参考代码保持一致：

```bash
python3 tests/validate_skills.py
```

## 参考文档

- [分层架构说明](./docs/architecture.md)
- [迁移说明](./docs/migration.md)
- [收钱吧 API Skills 说明](./sqb-api-skills/README.md)
