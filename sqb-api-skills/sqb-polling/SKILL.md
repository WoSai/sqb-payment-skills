---
name: sqb-polling
description: "收钱吧轮询框架。当用户需要单独生成轮询机制、自动查询、polling 逻辑时触发。"
version: "1.0"
tags: [polling, retry, query, async, utility]
globs: ["**/*.java", "**/*.py", "**/*.kt", "**/*.go"]
---

# 收钱吧轮询框架

## 引导词

- 轮询框架
- polling
- 轮询机制
- 自动查询
- 轮询策略
- poll until final
- 轮询逻辑
- 轮询间隔
- 支付轮询配置

## 概述

收钱吧交易接口的响应可能是非最终状态（如 PAY_IN_PROGRESS），此时必须启动自动轮询查询来获取最终结果。轮询框架提供参数化的两阶段轮询策略，支持不同交易场景的差异化配置。

## 轮询策略

### 两阶段自适应间隔

```
阶段           条件              间隔
第一阶段       elapsed < phase1Duration   phase1Interval
第二阶段       elapsed ≥ phase1Duration   phase2Interval
超时           elapsed > maxTimeout       停止轮询
```

### 预定义策略

| 策略 | 第一阶段 | 间隔 | 第二阶段间隔 | 总超时 | 适用场景 |
|---|---|---|---|---|---|
| PAY_POLLING_CONFIG | 0~60s | 3s | 10s | 120s | B扫C 付款码支付 |
| PRECREATE_POLLING_CONFIG | 0~30s | 2s | 5s | 240s | C扫B 预下单（等待扫码） |

### 超时处理

- 轮询超时后返回 TIMEOUT 状态（不抛异常）
- 由调用方决定是否继续等待、提示人工确认、或发起撤单
- 建议在前台 60 秒左右弹出超时提示

## 生成规则

当用户需要单独生成轮询模块时，**必须**包含：

1. `PollingConfig` 配置类：含 phase1Duration、phase1Interval、phase2Interval、maxTimeout 四个参数
2. `PAY_POLLING_CONFIG` 预定义配置：phase1=60s, interval=3s, phase2=10s, max=120s
3. `PRECREATE_POLLING_CONFIG` 预定义配置：phase1=30s, interval=2s, phase2=5s, max=240s
4. `pollUntilFinal(queryFn, config, callback)` 函数：
   - 接受查询函数（无参调用，返回查询结果）和配置参数
   - 两阶段自适应间隔
   - 超时后返回 TIMEOUT 状态，不抛异常
   - 查询异常时不中断轮询，继续重试
   - 支持回调通知每次轮询结果
5. `PollingResult` 结果类：含 status(SUCCESS/FAIL/TIMEOUT)、orderStatus、elapsedSeconds、pollCount、message

## 代码示例

见 `reference/` 目录：
- `SqbPollingUtil.java` — Java 轮询框架
- `sqb_polling_util.py` — Python 轮询框架
