<template>
  <div class="cashier-app">
    <header class="cashier-header">
      <h1>收钱吧收银台</h1>
      <span class="operator">操作员: {{ operator }}</span>
    </header>

    <main class="cashier-main">
      <!-- 金额输入区 -->
      <section class="amount-section">
        <div class="amount-display">
          <span class="currency">¥</span>
          <span class="amount">{{ displayAmount }}</span>
        </div>
        <div class="numpad">
          <button v-for="key in numKeys" :key="key" @click="inputAmount(key)" class="num-btn">
            {{ key }}
          </button>
          <button @click="clearAmount" class="num-btn clear-btn">C</button>
          <button @click="inputAmount('0')" class="num-btn">0</button>
          <button @click="inputAmount('.')" class="num-btn">.</button>
        </div>
      </section>

      <!-- 扫码支付区 -->
      <section class="scan-section">
        <div v-if="status === 'idle'" class="scan-input-area">
          <input
            ref="barcodeInput"
            v-model="barcode"
            @keydown.enter="submitPayment"
            placeholder="扫描付款码或手动输入"
            class="barcode-input"
            autofocus
          />
          <button @click="submitPayment" :disabled="!canPay" class="pay-btn">
            收款 ¥{{ displayAmount }}
          </button>
        </div>

        <!-- 支付状态展示 -->
        <div v-else class="status-display">
          <!-- 支付中 -->
          <div v-if="status === 'processing'" class="status-processing">
            <div class="spinner"></div>
            <p>支付处理中...</p>
            <p v-if="waitingPassword" class="hint">请顾客在手机上输入密码</p>
            <p class="elapsed">已等待 {{ elapsedSeconds }} 秒</p>
          </div>

          <!-- 支付成功 -->
          <div v-if="status === 'success'" class="status-success">
            <div class="icon-success">✓</div>
            <p class="result-amount">¥{{ displayAmount }}</p>
            <p>支付成功</p>
            <div class="action-buttons">
              <button @click="printReceipt" class="action-btn">打印小票</button>
              <button @click="reset" class="action-btn primary">下一笔</button>
            </div>
          </div>

          <!-- 支付失败 -->
          <div v-if="status === 'failed'" class="status-failed">
            <div class="icon-failed">✗</div>
            <p>{{ errorMessage }}</p>
            <div class="action-buttons">
              <button @click="reset" class="action-btn primary">重新收款</button>
            </div>
          </div>

          <!-- 超时 -->
          <div v-if="status === 'timeout'" class="status-timeout">
            <p>交易超时</p>
            <div class="action-buttons">
              <button @click="continuePolling" class="action-btn">继续等待</button>
              <button @click="reset" class="action-btn primary">取消交易</button>
            </div>
          </div>
        </div>
      </section>

      <!-- 订单信息 -->
      <section v-if="lastOrder" class="order-info">
        <h3>最近交易</h3>
        <p>订单号: {{ lastOrder.client_sn }}</p>
        <p>金额: ¥{{ fenToYuan(lastOrder.total_amount) }}</p>
        <p>状态: {{ lastOrder.order_status }}</p>
        <button v-if="lastOrder.order_status === 'PAID'" @click="refundOrder" class="refund-btn">
          退款
        </button>
      </section>
    </main>
  </div>
</template>

<script>
export default {
  name: 'CashierApp',
  data() {
    return {
      operator: 'cashier_01',
      amountStr: '',
      barcode: '',
      status: 'idle', // idle, processing, success, failed, timeout
      errorMessage: '',
      waitingPassword: false,
      elapsedSeconds: 0,
      lastOrder: null,
      pollingTimer: null,
      elapsedTimer: null,
      numKeys: ['1', '2', '3', '4', '5', '6', '7', '8', '9'],
    }
  },

  computed: {
    displayAmount() {
      return this.amountStr || '0.00'
    },
    canPay() {
      return parseFloat(this.amountStr) > 0 && this.barcode.length > 10
    },
    amountInFen() {
      // 元转分，避免浮点精度问题
      return Math.round(parseFloat(this.amountStr || '0') * 100).toString()
    },
  },

  methods: {
    inputAmount(key) {
      if (key === '.' && this.amountStr.includes('.')) return
      if (this.amountStr.includes('.') && this.amountStr.split('.')[1].length >= 2) return
      this.amountStr += key
    },

    clearAmount() {
      this.amountStr = ''
    },

    async submitPayment() {
      if (!this.canPay) return

      this.status = 'processing'
      this.elapsedSeconds = 0
      this.startElapsedTimer()

      try {
        // 调用后端支付接口
        const response = await fetch('/api/pay', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            total_amount: this.amountInFen,
            dynamic_id: this.barcode.trim(),
            subject: '门店消费',
            operator: this.operator,
          }),
        })

        const result = await response.json()

        if (result.status === 'SUCCESS') {
          this.onPaySuccess(result.data)
        } else if (result.status === 'PENDING') {
          // 启动前端轮询
          this.startPolling(result.data.client_sn)
        } else {
          this.onPayFailed(result.message || '支付失败')
        }
      } catch (error) {
        this.onPayFailed('网络错误: ' + error.message)
      }
    },

    startPolling(clientSn) {
      const startTime = Date.now()

      const poll = async () => {
        try {
          const response = await fetch(`/api/query?client_sn=${clientSn}`)
          const result = await response.json()
          const orderStatus = result.data?.order_status

          if (orderStatus === 'PAID') {
            this.onPaySuccess(result.data)
            return
          } else if (orderStatus === 'PAY_CANCELED') {
            this.onPayFailed('支付已取消')
            return
          }

          const elapsed = (Date.now() - startTime) / 1000

          // 60秒超时提示
          if (elapsed > 60 && this.status !== 'timeout') {
            this.status = 'timeout'
            this.stopElapsedTimer()
            return
          }

          // 继续轮询
          const interval = elapsed < 60 ? 3000 : 10000
          this.pollingTimer = setTimeout(poll, interval)
        } catch {
          // 查询失败，继续重试
          this.pollingTimer = setTimeout(poll, 3000)
        }
      }

      this.pollingTimer = setTimeout(poll, 3000)
    },

    continuePolling() {
      this.status = 'processing'
      this.startElapsedTimer()
      // 继续轮询（使用上次的 client_sn）
    },

    onPaySuccess(data) {
      this.status = 'success'
      this.lastOrder = data
      this.stopPolling()
      this.stopElapsedTimer()
    },

    onPayFailed(message) {
      this.status = 'failed'
      this.errorMessage = message
      this.stopPolling()
      this.stopElapsedTimer()
    },

    reset() {
      this.status = 'idle'
      this.amountStr = ''
      this.barcode = ''
      this.errorMessage = ''
      this.waitingPassword = false
      this.elapsedSeconds = 0
      this.stopPolling()
      this.stopElapsedTimer()
      this.$nextTick(() => this.$refs.barcodeInput?.focus())
    },

    startElapsedTimer() {
      this.elapsedTimer = setInterval(() => {
        this.elapsedSeconds++
      }, 1000)
    },

    stopElapsedTimer() {
      clearInterval(this.elapsedTimer)
    },

    stopPolling() {
      clearTimeout(this.pollingTimer)
    },

    printReceipt() {
      // TODO: 调用打印服务
      window.print()
    },

    async refundOrder() {
      if (!this.lastOrder) return
      if (!confirm('确认退款？')) return

      try {
        const response = await fetch('/api/refund', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sn: this.lastOrder.sn,
            refund_amount: this.lastOrder.total_amount,
            operator: this.operator,
          }),
        })
        const result = await response.json()
        alert(result.message || '退款已提交')
      } catch (error) {
        alert('退款请求失败: ' + error.message)
      }
    },

    fenToYuan(fen) {
      return (parseInt(fen) / 100).toFixed(2)
    },
  },

  mounted() {
    // 保持扫码输入框聚焦
    this.$refs.barcodeInput?.focus()
  },

  beforeUnmount() {
    this.stopPolling()
    this.stopElapsedTimer()
  },
}
</script>

<style scoped>
.cashier-app {
  max-width: 800px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

.cashier-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #1a73e8;
  color: white;
}

.amount-display {
  text-align: center;
  padding: 24px;
  font-size: 48px;
  font-weight: bold;
}

.currency {
  font-size: 24px;
  vertical-align: top;
}

.numpad {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 16px;
}

.num-btn {
  padding: 16px;
  font-size: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
}

.barcode-input {
  width: 100%;
  padding: 12px;
  font-size: 18px;
  border: 2px solid #1a73e8;
  border-radius: 8px;
  margin-bottom: 16px;
}

.pay-btn {
  width: 100%;
  padding: 16px;
  font-size: 20px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.pay-btn:disabled {
  background: #ccc;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #ddd;
  border-top-color: #1a73e8;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.icon-success {
  font-size: 64px;
  color: #34a853;
}

.icon-failed {
  font-size: 64px;
  color: #ea4335;
}

.status-display {
  text-align: center;
  padding: 48px 16px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
}

.action-btn {
  padding: 12px 24px;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
}

.action-btn.primary {
  background: #1a73e8;
  color: white;
  border: none;
}

.refund-btn {
  margin-top: 8px;
  padding: 8px 16px;
  background: #ea4335;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
