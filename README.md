# 收钱吧支付 Skills（shouqianba-payment-skills）

> 将收钱吧支付 API 对接知识封装为 AI Agent 可消费的 SKILL.md 格式，让 Claude Code / Cursor / OpenClaw / Codex 等 AI 编码助手通过自然语言指令自动生成符合规范的对接代码。

## 适用场景

- **B扫C（付款码支付）**：商户扫描顾客手机上的付款码完成收款
- **C扫B（预下单）**：商户生成二维码，顾客扫码支付

## 技能包结构

```
shouqianba-payment-skills/
├── README.md                          # 本文件
├── sqb-api-skills/                    # 后端技能包
│   ├── README.md
│   ├── shared-reference/              # 共享工具类（签名/状态判定/轮询）
│   │   ├── SqbSignUtil.java           # 签名工具（Java）
│   │   ├── sqb_sign_util.py           # 签名工具（Python）
│   │   ├── SqbStatusUtil.java         # 三层状态判定（Java）
│   │   ├── sqb_status_util.py         # 三层状态判定（Python）
│   │   ├── SqbPollingUtil.java        # 参数化轮询框架（Java）
│   │   └── sqb_polling_util.py        # 参数化轮询框架（Python）
│   ├── sqb-activate/                  # 终端激活
│   ├── sqb-checkin/                   # 终端签到（含密钥轮换容灾）
│   ├── sqb-pay/                       # B扫C 付款码支付（核心）
│   ├── sqb-precreate/                 # C扫B 预下单（二维码支付）
│   ├── sqb-query/                     # 订单查询
│   ├── sqb-refund/                    # 退款（支持部分退款）
│   ├── sqb-cancel/                    # 撤单/冲正
│   ├── sqb-notify/                    # 回调通知（RSA 验签）
│   ├── sqb-signing/                   # [共享模块] MD5 请求签名
│   ├── sqb-status-parsing/            # [共享模块] 三层状态判定
│   ├── sqb-polling/                   # [共享模块] 参数化轮询框架
│   └── sqb-callback-verify/           # [共享模块] RSA 回调验签
├── sqb-web-skills/                    # 前端技能包
│   └── sqb-cashier-ui/               # 收银台 UI 组件
│       ├── SKILL.md
│       └── reference/
│           ├── CashierApp.vue         # Vue 3 实现
│           ├── CashierApp.tsx         # React + TypeScript 实现
│           └── cashier-app.html       # 原生 JS 实现（零依赖）
└── tests/
    └── validate_skills.py             # 项目验证测试
```

## 安装指引

### Claude Code

```bash
# 方式一：克隆到项目目录
git clone https://github.com/anthropics/sqb-payment-skills.git

# 方式二：复制到全局 skills 目录
cp -r sqb-api-skills/ ~/.claude/skills/
cp -r sqb-web-skills/ ~/.claude/skills/
```

**验证**：在 Claude Code 中输入 "收钱吧支付" 或 "帮我用 Java 接入收钱吧付款码支付"，应触发 sqb-pay skill 并生成包含签名、三层状态判定、轮询的完整代码。

### Cursor

```bash
# 将技能包目录添加到项目根目录
cp -r sqb-api-skills/ your-project/
# 或在 .cursorrules 中引用 SKILL.md 路径
```

**验证**：在 Cursor Chat 中输入 "收钱吧退款"，应生成包含退款金额校验和异步轮询的代码。

### OpenClaw / Codex

将各 SKILL.md 文件添加到项目上下文或 system prompt 中。AI 工具会自动识别触发词并引用 reference 代码生成实现。

## 核心概念

### 终端体系

收钱吧采用 **服务商(vendor) → 商户(merchant) → 门店(store) → 终端(terminal)** 的四级体系：

- **vendor_sn / vendor_key**：服务商凭证，用于激活接口签名
- **terminal_sn / terminal_key**：终端凭证，用于交易接口签名（激活后获得）

### 签名机制

所有交易接口使用统一的签名方式（`shared-reference/SqbSignUtil`）：

```
Authorization: {terminal_sn} {MD5(request_body + terminal_key)}
```

> 签名工具类已模板化，生成代码时直接引用 `shared-reference/SqbSignUtil`，不要自行编写。

### 交易结果判定

三层状态判定（`shared-reference/SqbStatusUtil`）：`result_code` → `biz_response.result_code` → `order_status`

| order_status | 类型 | 处理方式 |
|---|---|---|
| `PAID` | 最终状态 | 支付成功 |
| `PAY_CANCELED` | 最终状态 | 支付失败 |
| `REFUNDED` | 最终状态 | 已全额退款 |
| `PARTIAL_REFUNDED` | 最终状态 | 已部分退款 |
| `CANCELED` | 最终状态 | 已撤销 |
| `CREATED` | 非最终状态 | 支付中，需轮询 |
| `PAY_ERROR` | 非最终状态 | 状态未知，需轮询 |

### 轮询策略

参数化轮询框架（`shared-reference/SqbPollingUtil`）：

| 场景 | 第一阶段 | 第二阶段 | 总超时 |
|---|---|---|---|
| B扫C 付款码支付 | 0~60s 每 3s | 60s+ 每 10s | 120s |
| C扫B 预下单 | 0~30s 每 2s | 30s+ 每 5s | 240s |

## 两种生成模式

本技能包支持**完整流程生成**和**单独模块生成**两种模式，开发者可以根据实际需求选择。

### 模式一：完整流程生成（默认）

当你需要从零接入一个接口时，使用完整流程触发词。AI 会生成该接口端到端的完整实现，包括签名、请求构建、响应解析、状态判定、轮询、异常处理等所有环节。

**触发方式**：使用接口名称或通用描述

| 你说的话 | 触发的 Skill | 生成内容 |
|---|---|---|
| "帮我用 Java 接入收钱吧付款码支付" | sqb-pay | 完整的 B扫C 支付流程（签名 + 请求 + 三层状态判定 + 轮询 + 异常处理） |
| "帮我实现收钱吧预下单" | sqb-precreate | 完整的 C扫B 预下单流程（签名 + 请求 + 二维码提取 + 轮询） |
| "帮我实现收钱吧退款功能" | sqb-refund | 完整的退款流程（签名 + 金额校验 + 请求 + 退款结果判定） |
| "帮我写收钱吧回调处理接口" | sqb-notify | 完整的回调处理（RSA 验签 + 幂等 + 状态分发 + 响应） |

### 模式二：单独模块生成

当你只需要某个特定功能模块时（例如已有项目中需要补充签名逻辑、或只需要实现轮询部分），使用模块级触发词。AI 只生成对应模块的代码，不会生成完整流程。

**触发方式**：在提示词中包含具体的模块名称

#### 接口内模块（每个接口 Skill 内置）

每个接口 Skill 的引导词分为「完整流程」和「单独模块」两组，使用单独模块的触发词即可按需生成：

| 接口 Skill | 可单独生成的模块 | 触发词示例 |
|---|---|---|
| sqb-pay | 支付请求构建、订单号生成、有密支付处理 | "支付请求构建"、"client_sn 生成"、"有密支付处理" |
| sqb-precreate | 预下单请求构建、二维码处理 | "预下单请求构建"、"qr_code 提取" |
| sqb-refund | 退款请求构建、退款金额校验、退款号生成 | "退款请求构建"、"累计退款校验"、"refund_request_no" |
| sqb-query | 查询请求构建、订单状态判定、轮询框架集成 | "查询请求构建"、"最终状态判定"、"polling集成" |
| sqb-cancel | 撤单请求构建、撤单结果判定、撤单后查询确认 | "撤单请求构建"、"cancel结果解析"、"cancel查询确认" |
| sqb-activate | Vendor 级别签名、激活请求构建、terminal_key 存储 | "vendor签名"、"激活请求构建"、"密钥持久化" |
| sqb-checkin | 签到请求构建、密钥轮换逻辑、双 key 容灾 | "签到请求构建"、"key rotation"、"签到容灾机制" |
| sqb-notify | RSA 回调验签、幂等处理、回调分发、公钥管理 | "回调验签"、"回调去重"、"状态分发逻辑"、"RSA公钥配置" |

#### 跨接口共享模块（独立 Skill）

以下 4 个通用模块被封装为独立的 Skill，不绑定任何特定接口，可以在任意场景下直接触发：

| 模块 Skill | 功能 | 触发词示例 | 典型使用场景 |
|---|---|---|---|
| sqb-signing | MD5 请求签名 + Authorization 头构建 | "收钱吧签名"、"MD5签名"、"Authorization头" | 已有 HTTP 客户端，只需补充签名逻辑 |
| sqb-status-parsing | 三层状态判定（result_code → biz_response → order_status） | "三层状态判定"、"状态解析"、"order_status判定" | 已有请求逻辑，需要补充响应解析 |
| sqb-polling | 参数化轮询框架（支持不同接口的轮询策略） | "轮询框架"、"polling"、"轮询策略" | 需要通用轮询能力，不限于特定接口 |
| sqb-callback-verify | RSA SHA256WithRSA 回调验签 | "RSA验签"、"回调验签"、"公钥验签" | 只需实现验签逻辑，已有回调接口框架 |

### 如何选择？

```
你的需求是什么？
│
├── 从零接入一个完整接口 → 模式一（完整流程）
│   示例："帮我用 Python 接入收钱吧付款码支付"
│
├── 已有项目，只缺某个功能模块 → 模式二（单独模块）
│   示例："帮我实现 MD5 签名工具类"
│
└── 已有部分实现，需要补充某个环节 → 模式二（单独模块）
    示例："帮我补充退款金额校验逻辑"
```

> **说明**：模式由 AI 根据你的提示词自动判定。当提示词中包含模块关键词（如"签名模块"、"请求构建"、"轮询逻辑"）时进入模块化模式；当提示词是通用的接口描述（如"收钱吧支付"）时进入完整流程模式。无需手动切换。

## 重要提醒

> **⚠️ 收钱吧没有沙盒环境。所有交易（包括使用测试激活码产生的交易）都是真实交易，会产生真实资金流动。测试完成后务必进行退款操作。**
>
> 每个 skill 生成的代码都会在类/模块注释中标注此警告，测试用例模板默认包含退款清理步骤。

## 接口调用顺序

```
激活(activate) → 签到(checkin) → 付款(pay/precreate) → 查询(query) → 退款(refund) / 撤单(cancel)
```

1. **激活**（一次性）：使用激活码获取 terminal_sn 和 terminal_key
2. **签到**（每天）：更新 terminal_key，保持终端活跃
3. **付款**：B扫C（pay）或 C扫B（precreate）
4. **查询 / 退款 / 撤单**：日常交易操作

## 技能优先级

| 优先级 | 技能 | 说明 |
|---|---|---|
| P0 | sqb-pay, sqb-precreate, sqb-query, sqb-refund | 完整收款-查询-退款闭环 |
| P1 | sqb-activate, sqb-checkin, sqb-cancel | 终端管理与资金安全保障 |
| P2 | sqb-notify | 异步回调通知处理（RSA 验签） |
| P3 | sqb-cashier-ui | 前端收银界面参考（Vue/React/原生JS） |

## API 域名

| 环境 | 域名 |
|---|---|
| 生产环境 | `https://vsi-api.shouqianba.com` |

## 验证测试

运行项目验证脚本确认所有 skill 结构正确、代码语法通过、API 路径一致：

```bash
python3 tests/validate_skills.py
```

| 测试项 | 说明 |
|---|---|
| 目录结构完整性 | 每个 skill 有 SKILL.md + reference 代码（含 4 个共享模块 skill） |
| SKILL.md 关键词覆盖 | 包含必要 API 参数和路径 |
| Python 语法检查 | py_compile 验证 |
| Java 结构检查 | class 定义 + 大括号匹配 |
| API 路径一致性 | 文档 vs 代码交叉验证 |
| 共享代码引用检查 | 交易类 SKILL.md 引用 shared-reference |
| 安全提醒检查 | 包含无沙盒警告 |
| 模块化生成章节 | 8 个接口 skill 均包含「模块化生成」章节及模块关键词 |
| 生成模式分区 | 8 个接口 skill 引导词均包含「完整流程」和「单独模块」分区 |
| 共享模块独立性 | 4 个共享模块 skill 各自包含 Java + Python 参考代码 |

## FAQ

### Q: 完整流程生成和单独模块生成有什么区别？

| 对比项 | 完整流程生成 | 单独模块生成 |
|---|---|---|
| 适用场景 | 从零接入一个接口 | 已有项目，补充某个功能模块 |
| 生成范围 | 签名 + 请求 + 响应解析 + 状态判定 + 轮询 + 异常处理 | 仅生成指定模块的代码片段 |
| 触发方式 | 通用描述（"收钱吧支付"） | 模块关键词（"支付请求构建"、"MD5签名"） |
| 代码量 | 完整的 Service + Controller + DTO + Util | 单个方法或工具类 |

两种模式由 AI 根据提示词自动判定，无需手动切换。详见上方「两种生成模式」章节。

### Q: Skill 触发不了怎么办？

1. 确认 SKILL.md 文件在 AI 工具的搜索路径中（Claude Code 的 skills 目录、Cursor 的项目目录等）
2. 尝试使用更明确的触发词，如 "收钱吧支付"、"sqb-pay"、"/upay/v2/pay"
3. 直接在 prompt 中引用 SKILL.md 文件路径

### Q: 生成的代码签名报错（ILLEGAL_SIGN）怎么排查？

检查以下三点（按频率排序）：
1. **body 一致性**：签名用的 body 字符串必须和实际发送的请求体**完全一致**（包括字段顺序、空格）
2. **编码问题**：body 必须是 UTF-8 编码，MD5 输出必须是 32 位**小写**十六进制
3. **key 过期**：terminal_key 每日自然日过期，确认已完成当日签到

### Q: 如何处理测试交易的退款清理？

收钱吧没有沙盒环境，所有交易都是真实的：
1. 测试金额建议使用 1 分钱（`total_amount: "1"`）
2. 测试完成后立即调用退款接口清理
3. 生成的代码模板中默认包含退款清理步骤
4. 超过 3 个月的交易无法退款，需线下处理

### Q: terminal_key 签名报 ILLEGAL_SIGN，签到也失败？

terminal_key 每日过期。如果签到也报签名错误：
1. 签到后服务端更新了 key，但本地未收到响应（网络异常）
2. 此时本地旧 key 已失效，新 key 未知
3. 利用双 key 机制窗口尝试用旧 key 重试
4. 如果仍然失败，需要**重新激活终端**（联系运营获取新激活码）
5. 详见 sqb-checkin 的密钥轮换容灾逻辑

### Q: B扫C 和 C扫B 有什么区别？

| 模式 | 接口 | 触发方 | 场景 |
|---|---|---|---|
| B扫C | sqb-pay | 商户扫顾客码 | 收银台扫码枪 |
| C扫B | sqb-precreate | 顾客扫商户码 | 桌面二维码牌 |

B扫C 实时扣款，C扫B 需要生成二维码后等待顾客扫码支付，轮询策略不同。

## 参考资源

- [收钱吧开发者文档](https://doc.shouqianba.com/)
- [收钱吧 GitHub (WoSai)](https://github.com/WoSai)
- [Java Demo](https://github.com/WoSai/Shouqianba-mobile-payment-API-demo-Java)
- [Python Demo](https://github.com/WoSai/Shouqianba-mobile-payment-API-demo-Python)
- [C# Demo](https://github.com/WoSai/Shouqianba-mobile-payment-API-demo-CSharp)
- [API 文档源码](https://github.com/WoSai/shouqianba-doc)
