# 分层架构说明

## 设计目标

本项目面向 AI 编码助手输出“收钱吧渠道适配层”代码，而不是只输出平铺示例类。

目标是让 AI 生成的代码天然带有以下特征：

- 分层清晰
- 共享能力可复用
- 安全边界显式可见
- 可以直接嵌入现有项目
- 保留完整流程生成与单独模块生成双模式

## 目标分层

### 1. protocol/client 层

职责：

- 发起 HTTP 请求
- 构建 Authorization 请求头
- 定义 request / response DTO
- 处理 vendor / terminal 凭证
- 处理 RSA 回调验签

典型文件：

- `SqbHttpClient`
- `SqbRequestSigner`
- `SqbCallbackVerifier`
- `PayRequest`, `PayResponse`

### 2. adapter 层

职责：

- 按收钱吧接口组织具体调用
- 封装 pay / precreate / query / refund / cancel / activate / checkin / notify
- 对外暴露稳定的 provider adapter 方法

典型文件：

- `SqbPaymentAdapter`
- `SqbPrecreateAdapter`
- `SqbQueryAdapter`
- `SqbRefundAdapter`
- `SqbTerminalAdapter`
- `SqbNotifyHandler`

### 3. support 层

职责：

- 三层状态解析
- 状态映射与最终状态判定
- 查询轮询
- 回调幂等
- terminal_key 轮换容灾

典型文件：

- `SqbStatusParser`
- `SqbPollingPolicy`
- `SqbPollingRunner`
- `SqbNotifyDeduplicator`
- `SqbKeyRotationSupport`

### 4. bootstrap 层

职责：

- 配置装配
- 控制器 / 路由入口
- 示例 Facade / Service
- 与具体框架衔接

典型文件：

- `SqbConfig`
- `SqbNotifyController`
- `SqbIntegrationFacade`

## 双模式生成

### 完整流程生成

输入是“收钱吧支付”“收钱吧退款”“收钱吧回调”这类完整需求时，AI 应输出：

- 对应接口的 `protocol` DTO / 请求执行逻辑
- `adapter` 层主实现
- 需要的 `support` 模块
- 最小 `bootstrap` 接入骨架

### 单独模块生成

输入是“MD5 签名”“轮询框架”“回调验签”“退款金额校验”时，AI 只输出：

- 对应层内的单模块代码
- 必要的输入输出契约
- 必要的引用说明

## 明确非目标

以下内容不属于本项目应生成的范围：

- 公司统一支付平台接口
- 多支付渠道汇总路由
- 风控 / 对账 / 清结算 / 账务引擎
- 组织级审计、监控、权限、任务平台

## 推荐输出目录

```text
shouqianba/
├── protocol/
├── adapter/
├── support/
└── bootstrap/
```

不同语言可以映射到各自惯用目录，但语义边界应保持一致。
