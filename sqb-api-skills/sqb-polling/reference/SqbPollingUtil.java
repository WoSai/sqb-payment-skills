package com.example.shouqianba.shared;

import java.util.function.Supplier;

/**
 * 收钱吧轮询框架
 *
 * ⚠️ 重要：不同交易场景使用不同的轮询参数，不要硬编码轮询间隔。
 *
 * 参数化轮询策略：
 *   pay（B扫C 付款码支付）：前 60s 每 3s，之后每 10s，总超时 120s
 *   precreate（C扫B 预下单）：前 30s 每 2s，之后每 5s，总超时 240s
 *
 * 超时后返回 TIMEOUT 状态，由调用方决定是否继续等待或发起撤单。
 */
public class SqbPollingUtil {

    /** 轮询策略配置 */
    public static class PollingConfig {
        public final int phase1Duration;   // 第一阶段持续时间（秒）
        public final int phase1Interval;   // 第一阶段轮询间隔（秒）
        public final int phase2Interval;   // 第二阶段轮询间隔（秒）
        public final int maxTimeout;       // 总超时时间（秒）

        public PollingConfig(int phase1Duration, int phase1Interval,
                             int phase2Interval, int maxTimeout) {
            this.phase1Duration = phase1Duration;
            this.phase1Interval = phase1Interval;
            this.phase2Interval = phase2Interval;
            this.maxTimeout = maxTimeout;
        }
    }

    /** B扫C 付款码支付轮询配置 */
    public static final PollingConfig PAY_POLLING_CONFIG =
        new PollingConfig(60, 3, 10, 120);

    /** C扫B 预下单轮询配置 */
    public static final PollingConfig PRECREATE_POLLING_CONFIG =
        new PollingConfig(30, 2, 5, 240);

    /** 轮询结果 */
    public static class PollingResult {
        public final String status;        // SUCCESS / FAIL / TIMEOUT
        public final String orderStatus;   // 原始订单状态
        public final double elapsedSeconds;
        public final int pollCount;
        public final String message;

        public PollingResult(String status, String orderStatus,
                             double elapsedSeconds, int pollCount, String message) {
            this.status = status;
            this.orderStatus = orderStatus;
            this.elapsedSeconds = elapsedSeconds;
            this.pollCount = pollCount;
            this.message = message;
        }

        @Override
        public String toString() {
            return "PollingResult{status='" + status + "', orderStatus='" + orderStatus
                + "', elapsed=" + String.format("%.1f", elapsedSeconds)
                + "s, polls=" + pollCount + ", message='" + message + "'}";
        }
    }

    /** 轮询回调接口 */
    @FunctionalInterface
    public interface PollCallback {
        void onPoll(int pollCount, double elapsedSeconds, String currentStatus);
    }

    /**
     * 参数化轮询框架：按配置的策略反复查询，直到获得最终状态或超时。
     *
     * @param queryFn  查询函数，返回订单的 order_status 字符串
     * @param config   轮询策略配置
     * @param callback 轮询回调（可为 null）
     * @return PollingResult
     */
    public static PollingResult pollUntilFinal(
            Supplier<String> queryFn,
            PollingConfig config,
            PollCallback callback) throws InterruptedException {

        long startTime = System.currentTimeMillis();
        int pollCount = 0;

        while (true) {
            double elapsed = (System.currentTimeMillis() - startTime) / 1000.0;

            // 超时检查
            if (elapsed > config.maxTimeout) {
                return new PollingResult("TIMEOUT", "", elapsed, pollCount,
                    "轮询超时（" + config.maxTimeout + "秒），请人工确认订单状态或发起撤单");
            }

            // 计算当前阶段的轮询间隔
            int interval = elapsed < config.phase1Duration
                ? config.phase1Interval : config.phase2Interval;
            Thread.sleep(interval * 1000L);

            // 执行查询
            pollCount++;
            String orderStatus;
            try {
                orderStatus = queryFn.get();
            } catch (Exception e) {
                if (callback != null) {
                    callback.onPoll(pollCount, (System.currentTimeMillis() - startTime) / 1000.0,
                        "查询异常: " + e.getMessage());
                }
                continue;
            }

            // 回调通知
            if (callback != null) {
                callback.onPoll(pollCount, (System.currentTimeMillis() - startTime) / 1000.0, orderStatus);
            }

            // 最终状态判定
            if (SqbStatusUtil.isFinalStatus(orderStatus)) {
                elapsed = (System.currentTimeMillis() - startTime) / 1000.0;
                String status;
                if ("PAID".equals(orderStatus) || "REFUNDED".equals(orderStatus)
                    || "PARTIAL_REFUNDED".equals(orderStatus) || "CANCELED".equals(orderStatus)) {
                    status = "SUCCESS";
                } else {
                    status = "FAIL";
                }
                return new PollingResult(status, orderStatus, elapsed, pollCount,
                    "订单状态: " + orderStatus);
            }
        }
    }
}
