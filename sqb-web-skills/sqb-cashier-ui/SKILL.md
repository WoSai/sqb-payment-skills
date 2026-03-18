---
name: sqb-cashier-ui
description: "[前端项目使用]收钱吧收银台前端UI组件技能。用于生成B扫C收银台界面，包含金额输入、扫码支付、状态展示等完整交互。当用户提到收银台界面、收银UI、cashier UI、POS界面、收款界面时触发。"
---

# 收钱吧收银台 UI 组件

## 引导词

- 收银台界面
- 收银UI
- cashier UI
- POS界面
- 收款界面
- 收银台组件

## 概述

为 B扫C（付款码支付）场景提供前端收银台界面参考实现，包含金额输入、扫码支付、状态展示、轮询等待等完整交互流程。

## 适用场景

- Web 端收银台（适用于 PC 浏览器 / 平板）
- 对接收钱吧后端 API（sqb-api-skills）的前端界面

## 核心交互流程

```
1. 输入/选择商品 → 显示总金额
2. 点击"收款" → 等待扫码
3. 扫码枪扫描付款码 → 自动提交支付
4. 显示"支付中..." → 轮询后端查询接口
5. 最终结果展示：
   - 支付成功 → 绿色成功页面 + 打印小票
   - 支付失败 → 红色失败提示 + 重试按钮
   - 超时 → 弹出确认框："继续等待" / "取消交易"
```

## UI 组件结构

```
CashierApp
├── AmountInput          # 金额输入区
│   ├── 数字键盘
│   └── 金额显示（元，自动转分）
├── PaymentPanel         # 支付操作区
│   ├── 扫码输入框（自动聚焦，接收扫码枪输入）
│   └── 手动输入付款码
├── StatusDisplay        # 状态展示区
│   ├── 支付中动画
│   ├── 等待密码输入提示
│   ├── 成功/失败结果
│   └── 超时确认对话框
├── OrderInfo            # 订单信息区
│   ├── 订单号
│   ├── 金额
│   └── 操作员
└── ActionBar            # 操作栏
    ├── 退款按钮
    ├── 查询按钮
    └── 打印小票按钮
```

## 关键交互细节

### 扫码输入

```javascript
// 扫码枪输入通常在 50-200ms 内连续输入完成
// 设置防抖检测扫码枪 vs 手动输入
const SCAN_THRESHOLD_MS = 200;
let inputBuffer = '';
let lastInputTime = 0;

function onBarcodeInput(char) {
    const now = Date.now();
    if (now - lastInputTime > SCAN_THRESHOLD_MS) {
        inputBuffer = '';  // 超过阈值，重置缓冲
    }
    inputBuffer += char;
    lastInputTime = now;

    // 扫码枪输入以回车结束
    if (char === '\n' && inputBuffer.length > 10) {
        submitPayment(inputBuffer.trim());
    }
}
```

### 支付状态轮询

```javascript
async function pollPaymentResult(clientSn) {
    const startTime = Date.now();

    while (true) {
        const result = await queryOrder(clientSn);
        const status = result.biz_response?.data?.order_status;

        // 最终状态
        if (['PAID', 'PAY_CANCELED'].includes(status)) {
            return result;
        }

        const elapsed = (Date.now() - startTime) / 1000;

        // 超时提示
        if (elapsed > 60 && !userConfirmedWait) {
            const shouldContinue = await showTimeoutDialog();
            if (!shouldContinue) {
                return { timeout: true };
            }
            userConfirmedWait = true;
        }

        // 轮询间隔
        const interval = elapsed < 60 ? 3000 : 10000;
        await sleep(interval);
    }
}
```

### 金额转换

```javascript
// 用户输入元，API 接收分
function yuanToFen(yuan) {
    // 使用整数运算避免浮点精度问题
    return Math.round(parseFloat(yuan) * 100).toString();
}

// API 返回分，显示为元
function fenToYuan(fen) {
    return (parseInt(fen) / 100).toFixed(2);
}
```

## 状态展示设计

| 状态 | UI 表现 | 操作 |
|---|---|---|
| 待扫码 | 扫码输入框聚焦，光标闪烁 | 等待扫码枪输入 |
| 支付中 | 旋转加载动画 + "支付处理中..." | 自动轮询 |
| 等待密码 | 手机图标 + "请顾客输入密码" | 自动轮询 |
| 支付成功 | 绿色对勾 + 金额 + 成功音效 | 显示打印按钮 |
| 支付失败 | 红色叉号 + 失败原因 | 显示重试按钮 |
| 超时 | 弹窗"交易超时" | 继续等待 / 取消 |

## 陷阱与注意事项

1. **扫码输入框必须保持聚焦**—— 扫码枪模拟键盘输入，焦点丢失会导致扫码失败
2. **金额精度**—— 使用整数（分）计算，避免浮点误差
3. **防重复提交**—— 提交后禁用按钮，防止重复扫码触发多次支付
4. **超时友好提示**—— 不要让收银员和顾客无限等待，60秒弹出确认
5. **支持键盘快捷键**—— 收银场景高频操作，建议支持快捷键（如 F1 收款、F2 退款）

## 生成规则

当生成收银台 UI 代码时，建议包含：
1. 扫码输入组件（自动聚焦 + 扫码枪识别）
2. 金额输入与元/分转换
3. 支付状态展示与轮询
4. 超时处理对话框
5. 响应式布局（适配不同屏幕）
6. 基础样式（可用 Tailwind CSS 或纯 CSS）

## 代码示例

见 `reference/` 目录：
- `CashierApp.vue` — Vue3 单文件组件完整实现
