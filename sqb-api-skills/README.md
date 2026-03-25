# 收钱吧后端技能包（sqb-api-skills）

本目录包含收钱吧支付场景的后端 API 对接技能，目标是指导 AI 生成**分层的渠道适配层代码**，而不是只输出单个示例类。

## 设计目标

每个后端 skill 都围绕以下统一架构组织输出：

- `protocol/client`：签名、验签、HTTP 调用、DTO
- `adapter`：对具体收钱吧接口的封装
- `support`：状态解析、轮询、幂等、密钥轮换
- `bootstrap`：配置、入口、示例 Facade / Controller

完整流程模式会按这个结构输出最小可落地骨架；单独模块模式只生成某一层或某个模块。

## 技能列表

| 技能 | 说明 | 推荐生成层 |
|---|---|---|
| [sqb-activate](./sqb-activate/) | 终端激活 | `protocol` + `adapter` + `bootstrap` |
| [sqb-checkin](./sqb-checkin/) | 终端签到（含密钥轮换容灾） | `protocol` + `adapter` + `support` |
| [sqb-pay](./sqb-pay/) | B扫C 付款码支付 | `protocol` + `adapter` + `support` |
| [sqb-precreate](./sqb-precreate/) | C扫B 预下单 | `protocol` + `adapter` + `support` |
| [sqb-query](./sqb-query/) | 订单查询 | `protocol` + `adapter` + `support` |
| [sqb-refund](./sqb-refund/) | 退款（支持部分退款） | `protocol` + `adapter` + `support` |
| [sqb-cancel](./sqb-cancel/) | 撤单/冲正 | `protocol` + `adapter` + `support` |
| [sqb-notify](./sqb-notify/) | 回调通知（RSA 验签） | `protocol` + `adapter` + `support` + `bootstrap` |

## 双模式生成

### 完整流程生成（默认）

适用于“从零接入一个接口”。

输出要求：

- 生成该接口对应的 `adapter`
- 生成最少必要的 `protocol` DTO 与请求执行逻辑
- 自动引入需要的 `support` 模块
- 给出可嵌入项目的 `bootstrap` 骨架

示例：

- “帮我用 Java 接入收钱吧付款码支付”
- “帮我实现收钱吧退款适配层”
- “帮我生成收钱吧回调完整接入”

### 单独模块生成

适用于“已有项目里补某个模块”。

输出要求：

- 只生成所请求模块
- 明确该模块所属层次
- 标注它依赖的共享能力或上游下游契约

示例：

- “帮我生成收钱吧请求签名层”
- “帮我补一个 query adapter”
- “帮我生成退款金额校验模块”
- “帮我写回调验签模块”

## 跨接口共享模块 Skill

以下 4 个通用模块被封装为独立 Skill，用于让 AI 在单独模块模式下生成可复用 building block：

| 技能 | 所属层 | 功能 |
|---|---|---|
| [sqb-signing](./sqb-signing/) | `protocol/security` | MD5 请求签名 + Authorization 头 |
| [sqb-status-parsing](./sqb-status-parsing/) | `support/status` | 三层状态判定 |
| [sqb-polling](./sqb-polling/) | `support/polling` | 参数化轮询框架 |
| [sqb-callback-verify](./sqb-callback-verify/) | `protocol/security` | RSA SHA256WithRSA 回调验签 |

## 共享参考代码

`shared-reference/` 目录保存跨 skill 共用的参考实现：

| 文件 | 定位 |
|---|---|
| `SqbSignUtil` / `sqb_sign_util.py` | 请求签名、Authorization 构造 |
| `SqbStatusUtil` / `sqb_status_util.py` | 三层状态解析与最终状态判定 |
| `SqbPollingUtil` / `sqb_polling_util.py` | 参数化轮询策略与执行器 |

生成代码时应优先复用这些共享能力，而不是在各 skill 内重复实现。

## 推荐落地目录

业务仓中推荐的放置方式如下：

```text
shouqianba/
├── protocol/
├── adapter/
├── support/
└── bootstrap/
```

不要把收钱吧字段和状态直接散落到订单、收银、退款等业务模块中。

## 通用规范

- 协议：HTTPS POST
- Content-Type：`application/json; charset=utf-8`
- 域名：`https://vsi-api.shouqianba.com`
- 所有交易相关 skill 必须保留“无沙盒环境”警告
- 回调相关 skill 必须强制生成 RSA 验签逻辑

## 推荐调用顺序

```text
sqb-activate → sqb-checkin → sqb-pay/sqb-precreate → sqb-query → sqb-refund/sqb-cancel
```
