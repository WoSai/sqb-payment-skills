// ⚠️ 收钱吧没有沙盒环境，此组件将发起真实交易

import React, { useState, useEffect, useCallback, useRef } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type PaymentStatus = 'idle' | 'processing' | 'success' | 'failed' | 'timeout';

interface OrderData {
  sn: string;
  client_sn: string;
  total_amount: string;
  order_status: string;
  [key: string]: unknown;
}

interface CashierAppProps {
  /** 操作员标识，默认 cashier_01 */
  operator?: string;
  /** 支付接口基础路径，默认 /api */
  apiBase?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** 元转分，避免浮点精度问题 */
function yuanToFen(yuan: string): string {
  return Math.round(parseFloat(yuan || '0') * 100).toString();
}

/** 分转元 */
function fenToYuan(fen: string | number): string {
  return (parseInt(String(fen), 10) / 100).toFixed(2);
}

// ---------------------------------------------------------------------------
// Styles (CSS-in-JS, self-contained)
// ---------------------------------------------------------------------------

const styles: Record<string, React.CSSProperties> = {
  app: {
    maxWidth: 800,
    margin: '0 auto',
    fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    background: '#1a73e8',
    color: 'white',
  },
  headerTitle: { margin: 0 },
  amountDisplay: {
    textAlign: 'center' as const,
    padding: 24,
    fontSize: 48,
    fontWeight: 'bold',
  },
  currency: { fontSize: 24, verticalAlign: 'top' as const },
  numpad: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 8,
    padding: 16,
  },
  numBtn: {
    padding: 16,
    fontSize: 20,
    border: '1px solid #ddd',
    borderRadius: 8,
    cursor: 'pointer',
    background: 'white',
  },
  clearBtn: { background: '#f5f5f5' },
  barcodeInput: {
    width: '100%',
    padding: 12,
    fontSize: 18,
    border: '2px solid #1a73e8',
    borderRadius: 8,
    marginBottom: 16,
    boxSizing: 'border-box' as const,
  },
  payBtn: {
    width: '100%',
    padding: 16,
    fontSize: 20,
    background: '#1a73e8',
    color: 'white',
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
  },
  payBtnDisabled: {
    width: '100%',
    padding: 16,
    fontSize: 20,
    background: '#ccc',
    color: 'white',
    border: 'none',
    borderRadius: 8,
    cursor: 'not-allowed',
  },
  statusDisplay: { textAlign: 'center' as const, padding: '48px 16px' },
  spinner: {
    width: 48,
    height: 48,
    border: '4px solid #ddd',
    borderTopColor: '#1a73e8',
    borderRadius: '50%',
    margin: '0 auto 16px',
    animation: 'sqb-spin 1s linear infinite',
  },
  iconSuccess: { fontSize: 64, color: '#34a853' },
  iconFailed: { fontSize: 64, color: '#ea4335' },
  actionButtons: {
    display: 'flex',
    gap: 12,
    justifyContent: 'center',
    marginTop: 24,
  },
  actionBtn: {
    padding: '12px 24px',
    border: '1px solid #ddd',
    borderRadius: 8,
    cursor: 'pointer',
    background: 'white',
  },
  actionBtnPrimary: {
    padding: '12px 24px',
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
    background: '#1a73e8',
    color: 'white',
  },
  orderInfo: { padding: 16, borderTop: '1px solid #eee', marginTop: 16 },
  refundBtn: {
    marginTop: 8,
    padding: '8px 16px',
    background: '#ea4335',
    color: 'white',
    border: 'none',
    borderRadius: 4,
    cursor: 'pointer',
  },
  hint: { color: '#666', fontSize: 14 },
  elapsed: { color: '#999', fontSize: 13 },
  resultAmount: { fontSize: 32, fontWeight: 'bold' as const },
  scanSection: { padding: 16 },
};

// Keyframe animation injected once
const SPIN_STYLE_ID = 'sqb-cashier-spin';
function ensureSpinKeyframes() {
  if (typeof document === 'undefined') return;
  if (document.getElementById(SPIN_STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = SPIN_STYLE_ID;
  style.textContent = `@keyframes sqb-spin { to { transform: rotate(360deg); } }`;
  document.head.appendChild(style);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const NUM_KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9'];

const CashierApp: React.FC<CashierAppProps> = ({
  operator = 'cashier_01',
  apiBase = '/api',
}) => {
  // --- State ---
  const [amountStr, setAmountStr] = useState('');
  const [barcode, setBarcode] = useState('');
  const [status, setStatus] = useState<PaymentStatus>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [waitingPassword, setWaitingPassword] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [lastOrder, setLastOrder] = useState<OrderData | null>(null);

  // --- Refs for timers (avoid stale closures) ---
  const pollingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const elapsedTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const barcodeInputRef = useRef<HTMLInputElement>(null);
  const submittingRef = useRef(false);

  // Inject keyframes on mount
  useEffect(() => {
    ensureSpinKeyframes();
  }, []);

  // --- Derived ---
  const displayAmount = amountStr || '0.00';
  const canPay = parseFloat(amountStr) > 0 && barcode.length > 10;

  // --- Timer helpers ---
  const stopPolling = useCallback(() => {
    if (pollingTimerRef.current !== null) {
      clearTimeout(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  }, []);

  const stopElapsedTimer = useCallback(() => {
    if (elapsedTimerRef.current !== null) {
      clearInterval(elapsedTimerRef.current);
      elapsedTimerRef.current = null;
    }
  }, []);

  const startElapsedTimer = useCallback(() => {
    stopElapsedTimer();
    elapsedTimerRef.current = setInterval(() => {
      setElapsedSeconds((s) => s + 1);
    }, 1000);
  }, [stopElapsedTimer]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
      stopElapsedTimer();
    };
  }, [stopPolling, stopElapsedTimer]);

  // --- Amount input ---
  const inputAmount = useCallback(
    (key: string) => {
      setAmountStr((prev) => {
        if (key === '.' && prev.includes('.')) return prev;
        if (prev.includes('.') && prev.split('.')[1].length >= 2) return prev;
        return prev + key;
      });
    },
    [],
  );

  const clearAmount = useCallback(() => setAmountStr(''), []);

  // --- Payment callbacks ---
  const onPaySuccess = useCallback(
    (data: OrderData) => {
      setStatus('success');
      setLastOrder(data);
      stopPolling();
      stopElapsedTimer();
      submittingRef.current = false;
    },
    [stopPolling, stopElapsedTimer],
  );

  const onPayFailed = useCallback(
    (message: string) => {
      setStatus('failed');
      setErrorMessage(message);
      stopPolling();
      stopElapsedTimer();
      submittingRef.current = false;
    },
    [stopPolling, stopElapsedTimer],
  );

  // --- Polling ---
  const startPolling = useCallback(
    (clientSn: string) => {
      const startTime = Date.now();

      const poll = async () => {
        try {
          const response = await fetch(`${apiBase}/query?client_sn=${clientSn}`);
          const result = await response.json();
          const orderStatus: string | undefined = result.data?.order_status;

          if (orderStatus === 'PAID') {
            onPaySuccess(result.data);
            return;
          }
          if (orderStatus === 'PAY_CANCELED') {
            onPayFailed('支付已取消');
            return;
          }

          const elapsed = (Date.now() - startTime) / 1000;

          if (elapsed > 60) {
            setStatus('timeout');
            stopElapsedTimer();
            return;
          }

          const interval = elapsed < 60 ? 3000 : 10000;
          pollingTimerRef.current = setTimeout(poll, interval);
        } catch {
          // 查询失败，继续重试
          pollingTimerRef.current = setTimeout(poll, 3000);
        }
      };

      pollingTimerRef.current = setTimeout(poll, 3000);
    },
    [apiBase, onPaySuccess, onPayFailed, stopElapsedTimer],
  );

  // --- Submit payment ---
  const submitPayment = useCallback(async () => {
    if (!canPay) return;
    if (submittingRef.current) return; // 防重复提交
    submittingRef.current = true;

    setStatus('processing');
    setElapsedSeconds(0);
    startElapsedTimer();

    try {
      const response = await fetch(`${apiBase}/pay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          total_amount: yuanToFen(amountStr),
          dynamic_id: barcode.trim(),
          subject: '门店消费',
          operator,
        }),
      });

      const result = await response.json();

      if (result.status === 'SUCCESS') {
        onPaySuccess(result.data);
      } else if (result.status === 'PENDING') {
        startPolling(result.data.client_sn);
      } else {
        onPayFailed(result.message || '支付失败');
      }
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      onPayFailed('网络错误: ' + msg);
    }
  }, [canPay, amountStr, barcode, operator, apiBase, startElapsedTimer, onPaySuccess, onPayFailed, startPolling]);

  // --- Continue polling (from timeout state) ---
  const continuePolling = useCallback(() => {
    setStatus('processing');
    startElapsedTimer();
    // 继续轮询（使用上次的 client_sn）
  }, [startElapsedTimer]);

  // --- Reset ---
  const reset = useCallback(() => {
    setStatus('idle');
    setAmountStr('');
    setBarcode('');
    setErrorMessage('');
    setWaitingPassword(false);
    setElapsedSeconds(0);
    stopPolling();
    stopElapsedTimer();
    submittingRef.current = false;
    // Auto-focus after state update
    setTimeout(() => barcodeInputRef.current?.focus(), 0);
  }, [stopPolling, stopElapsedTimer]);

  // --- Print receipt ---
  const printReceipt = useCallback(() => {
    // TODO: 调用打印服务
    window.print();
  }, []);

  // --- Refund ---
  const refundOrder = useCallback(async () => {
    if (!lastOrder) return;
    if (!window.confirm('确认退款？')) return;

    try {
      const response = await fetch(`${apiBase}/refund`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sn: lastOrder.sn,
          refund_amount: lastOrder.total_amount,
          operator,
        }),
      });
      const result = await response.json();
      window.alert(result.message || '退款已提交');
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      window.alert('退款请求失败: ' + msg);
    }
  }, [lastOrder, apiBase, operator]);

  // Auto-focus barcode input on mount and when returning to idle
  useEffect(() => {
    if (status === 'idle') {
      barcodeInputRef.current?.focus();
    }
  }, [status]);

  // --- Render helpers ---
  const handleBarcodeKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      submitPayment();
    }
  };

  // --- Render ---
  return (
    <div style={styles.app}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.headerTitle}>收钱吧收银台</h1>
        <span>操作员: {operator}</span>
      </header>

      <main>
        {/* 金额输入区 */}
        <section>
          <div style={styles.amountDisplay}>
            <span style={styles.currency}>¥</span>
            <span>{displayAmount}</span>
          </div>
          <div style={styles.numpad}>
            {NUM_KEYS.map((key) => (
              <button key={key} style={styles.numBtn} onClick={() => inputAmount(key)}>
                {key}
              </button>
            ))}
            <button style={{ ...styles.numBtn, ...styles.clearBtn }} onClick={clearAmount}>
              C
            </button>
            <button style={styles.numBtn} onClick={() => inputAmount('0')}>
              0
            </button>
            <button style={styles.numBtn} onClick={() => inputAmount('.')}>
              .
            </button>
          </div>
        </section>

        {/* 扫码支付区 */}
        <section style={styles.scanSection}>
          {status === 'idle' ? (
            <div>
              <input
                ref={barcodeInputRef}
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
                onKeyDown={handleBarcodeKeyDown}
                placeholder="扫描付款码或手动输入"
                style={styles.barcodeInput}
                autoFocus
              />
              <button
                onClick={submitPayment}
                disabled={!canPay}
                style={canPay ? styles.payBtn : styles.payBtnDisabled}
              >
                收款 ¥{displayAmount}
              </button>
            </div>
          ) : (
            <div style={styles.statusDisplay}>
              {/* 支付中 */}
              {status === 'processing' && (
                <div>
                  <div style={styles.spinner} />
                  <p>支付处理中...</p>
                  {waitingPassword && <p style={styles.hint}>请顾客在手机上输入密码</p>}
                  <p style={styles.elapsed}>已等待 {elapsedSeconds} 秒</p>
                </div>
              )}

              {/* 支付成功 */}
              {status === 'success' && (
                <div>
                  <div style={styles.iconSuccess}>✓</div>
                  <p style={styles.resultAmount}>¥{displayAmount}</p>
                  <p>支付成功</p>
                  <div style={styles.actionButtons}>
                    <button style={styles.actionBtn} onClick={printReceipt}>
                      打印小票
                    </button>
                    <button style={styles.actionBtnPrimary} onClick={reset}>
                      下一笔
                    </button>
                  </div>
                </div>
              )}

              {/* 支付失败 */}
              {status === 'failed' && (
                <div>
                  <div style={styles.iconFailed}>✗</div>
                  <p>{errorMessage}</p>
                  <div style={styles.actionButtons}>
                    <button style={styles.actionBtnPrimary} onClick={reset}>
                      重新收款
                    </button>
                  </div>
                </div>
              )}

              {/* 超时 */}
              {status === 'timeout' && (
                <div>
                  <p>交易超时</p>
                  <div style={styles.actionButtons}>
                    <button style={styles.actionBtn} onClick={continuePolling}>
                      继续等待
                    </button>
                    <button style={styles.actionBtnPrimary} onClick={reset}>
                      取消交易
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* 订单信息 */}
        {lastOrder && (
          <section style={styles.orderInfo}>
            <h3>最近交易</h3>
            <p>订单号: {lastOrder.client_sn}</p>
            <p>金额: ¥{fenToYuan(lastOrder.total_amount)}</p>
            <p>状态: {lastOrder.order_status}</p>
            {lastOrder.order_status === 'PAID' && (
              <button style={styles.refundBtn} onClick={refundOrder}>
                退款
              </button>
            )}
          </section>
        )}
      </main>
    </div>
  );
};

export default CashierApp;
