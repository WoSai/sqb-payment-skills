# 收钱吧支付 Skills（shouqianba-payment-skills）

> 将收钱吧支付 API 对接知识封装为 AI Agent 可消费的 SKILL.md 格式，让 Claude Code / Cursor / Trae / OpenClaw / Codex 等 AI 编码助手通过自然语言指令自动生成符合规范的对接代码。

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
│   └── sqb-notify/                    # 回调通知（RSA 验签）
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

### Trae

将 `sqb-api-skills/` 目录添加到 Trae 工作区的 skills 目录中。

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
| 目录结构完整性 | 每个 skill 有 SKILL.md + reference 代码 |
| SKILL.md 关键词覆盖 | 包含必要 API 参数和路径 |
| Python 语法检查 | py_compile 验证 |
| Java 结构检查 | class 定义 + 大括号匹配 |
| API 路径一致性 | 文档 vs 代码交叉验证 |
| 共享代码引用检查 | 交易类 SKILL.md 引用 shared-reference |
| 安全提醒检查 | 包含无沙盒警告 |

## FAQ

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
