---
name: sqb-cashier-ui
description: "[前端项目使用]收钱吧收银台前端 UI 组件技能。用于生成收银台界面，并与后端 adapter/facade 层对接。"
version: "2.0"
tags: [frontend, cashier, ui, pos]
globs: ["**/*.vue", "**/*.tsx", "**/*.jsx", "**/*.html"]
---

# 收钱吧收银台 UI 组件

## 边界定位

本 skill 负责生成前端收银台 UI 与交互，不直接生成收钱吧协议调用。

推荐依赖的后端边界是：

- 你们项目中的 `bootstrap/facade`
- 或你们暴露给前端的统一支付接口

前端不应该直接感知：

- `terminal_key`
- MD5 签名
- RSA 验签
- 收钱吧原始协议细节

## 引导词

- 收银台界面
- 收银UI
- cashier UI
- POS界面
- 收款界面
- 收银台组件
- POS component
- 收款界面组件
- barcode scanner UI

## 核心交互流程

```text
1. 输入金额
2. 点击收款或等待扫码枪输入
3. 调用你们自己的支付接入接口
4. 轮询你们自己的查询接口或等待后端推送
5. 展示支付成功 / 失败 / 超时
```

## 生成规则

1. 必须生成扫码输入组件
2. 必须生成金额输入与元/分转换
3. 必须生成支付中、等待密码、成功、失败、超时等状态展示
4. 必须明确前端调用的是你们自己的后端 facade / API
5. 不要在前端内生成收钱吧签名或供应商协议调用

## 技术栈变体

- Vue 项目：参考 `CashierApp.vue`
- React 项目：参考 `CashierApp.tsx`
- 原生项目：参考 `cashier-app.html`
