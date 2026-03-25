# 迁移说明

## 为什么需要迁移

旧版 skills 更偏向“接口示例 + 工具示例”，适合作为 AI 参考，但对真实项目落地时的分层约束不够强。

新版 skills 继续保留：

- 完整流程生成
- 单独模块生成
- Java / Python 参考代码

同时新增：

- 明确的生成边界
- 面向 adapter / integration layer 的分层输出契约
- 更统一的共享模块定位

## 迁移原则

### 原有 skill 名称保持不变

以下 skill 继续保留，不要求用户更换调用词：

- `sqb-activate`
- `sqb-checkin`
- `sqb-pay`
- `sqb-precreate`
- `sqb-query`
- `sqb-refund`
- `sqb-cancel`
- `sqb-notify`
- `sqb-signing`
- `sqb-status-parsing`
- `sqb-polling`
- `sqb-callback-verify`

### 原有两种模式保持不变

- 通用接口描述 → 完整流程生成
- 模块关键词 → 单独模块生成

### 主要变化

旧版倾向生成：

- `PayExample`
- `RefundExample`
- `NotifyExample`

新版倾向生成：

- `protocol/*`
- `adapter/*`
- `support/*`
- `bootstrap/*`

## 对现有用户的建议

如果你已经在项目中使用旧版 skill：

1. 可以继续使用原有触发词。
2. 建议将新生成代码放到渠道适配层目录，而不是业务核心目录。
3. 建议把旧的示例式实现逐步迁移为 `client + adapter + support` 分层。

## 兼容性说明

本次迁移不会移除旧 skill 名称，也不会取消任何现有 API 覆盖范围。

改变的是推荐产物的组织方式与生成契约，而不是收钱吧接口能力本身。
