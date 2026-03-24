package com.example.shouqianba.shared;

import java.util.Set;

/**
 * 收钱吧三层状态判定工具
 *
 * ⚠️ 重要：所有交易类 skill 共享此状态判定实现，不要自行重新实现判定逻辑。
 *
 * 三层判定模型：
 *   第一层 result_code          → 通信层（200=成功，其他=通信失败）
 *   第二层 biz_response.result_code → 业务层（PAY_SUCCESS/PAY_FAIL 等）
 *   第三层 order_status          → 订单最终状态（PAID/PAY_CANCELED 等）
 *
 * 最终状态（不可变）：PAID, PAY_CANCELED, REFUNDED, PARTIAL_REFUNDED, CANCELED
 * 非最终状态（需轮询）：CREATED, PAY_ERROR, REFUND_ERROR, CANCEL_ERROR
 */
public class SqbStatusUtil {

    /** 最终状态集合——收到这些状态后可以停止轮询 */
    public static final Set<String> FINAL_ORDER_STATUSES = Set.of(
        "PAID", "PAY_CANCELED", "REFUNDED", "PARTIAL_REFUNDED", "CANCELED"
    );

    /** 业务层确定失败码（不需要轮询） */
    public static final Set<String> BIZ_DEFINITE_FAIL_CODES = Set.of(
        "PAY_FAIL", "PRECREATE_FAIL", "REFUND_FAIL", "CANCEL_ABORT_ERROR", "FAIL"
    );

    /** 业务层不确定状态码（需要轮询确认） */
    public static final Set<String> BIZ_UNCERTAIN_CODES = Set.of(
        "PAY_FAIL_ERROR", "PAY_IN_PROGRESS", "REFUND_IN_PROGRESS",
        "REFUND_FAIL_ERROR", "CANCEL_ERROR"
    );

    /** 判断 order_status 是否为最终状态 */
    public static boolean isFinalStatus(String orderStatus) {
        return orderStatus != null && FINAL_ORDER_STATUSES.contains(orderStatus);
    }

    /**
     * 三层状态判定结果
     */
    public static class ParsedResponse {
        public final String status;       // SUCCESS / FAIL / PENDING
        public final String orderStatus;  // 原始 order_status 值
        public final String sn;           // 收钱吧订单号
        public final String clientSn;     // 商户订单号
        public final String message;      // 人类可读的状态描述
        public final boolean isFinal;     // 是否为最终状态

        public ParsedResponse(String status, String orderStatus, String sn,
                              String clientSn, String message, boolean isFinal) {
            this.status = status;
            this.orderStatus = orderStatus;
            this.sn = sn;
            this.clientSn = clientSn;
            this.message = message;
            this.isFinal = isFinal;
        }

        @Override
        public String toString() {
            return "ParsedResponse{status='" + status + "', orderStatus='" + orderStatus
                + "', sn='" + sn + "', message='" + message + "', isFinal=" + isFinal + "}";
        }
    }

    /**
     * 三层状态判定：解析收钱吧 API 响应
     *
     * 使用 Jackson JsonNode 作为输入参数。
     * 示例用法：
     *   JsonNode resp = mapper.readTree(responseBody);
     *   ParsedResponse parsed = SqbStatusUtil.parseResponse(resp);
     *
     * @param resultCode      顶层 result_code
     * @param errorCode       顶层 error_code（通信失败时有值）
     * @param errorMessage    顶层 error_message
     * @param bizResultCode   biz_response.result_code
     * @param bizErrorMessage biz_response.error_message
     * @param orderStatus     biz_response.data.order_status
     * @param sn              biz_response.data.sn
     * @param clientSn        biz_response.data.client_sn
     */
    public static ParsedResponse parseResponse(
            String resultCode, String errorCode, String errorMessage,
            String bizResultCode, String bizErrorMessage,
            String orderStatus, String sn, String clientSn) {

        // ── 第一层：通信层 ──
        if (!"200".equals(resultCode)) {
            return new ParsedResponse("FAIL", "", "", "",
                "通信失败[" + errorCode + "]: " + errorMessage, true);
        }

        // ── 第二层：业务层 ──
        if (BIZ_DEFINITE_FAIL_CODES.contains(bizResultCode)) {
            String msg = bizErrorMessage != null ? bizErrorMessage : bizResultCode;
            return new ParsedResponse("FAIL", "", "", "",
                "业务失败: " + msg, true);
        }

        if (BIZ_UNCERTAIN_CODES.contains(bizResultCode)) {
            return new ParsedResponse("PENDING", "", "", "",
                "状态不确定[" + bizResultCode + "]，需轮询查询", false);
        }

        // ── 第三层：订单状态 ──
        if ("PAID".equals(orderStatus)) {
            return new ParsedResponse("SUCCESS", orderStatus, sn, clientSn, "支付成功", true);
        } else if ("PAY_CANCELED".equals(orderStatus)) {
            return new ParsedResponse("FAIL", orderStatus, sn, clientSn, "支付已撤销", true);
        } else if ("REFUNDED".equals(orderStatus)) {
            return new ParsedResponse("SUCCESS", orderStatus, sn, clientSn, "全额退款成功", true);
        } else if ("PARTIAL_REFUNDED".equals(orderStatus)) {
            return new ParsedResponse("SUCCESS", orderStatus, sn, clientSn, "部分退款成功", true);
        } else if ("CANCELED".equals(orderStatus)) {
            return new ParsedResponse("SUCCESS", orderStatus, sn, clientSn, "订单已撤销", true);
        } else {
            return new ParsedResponse("PENDING", orderStatus, sn, clientSn,
                "状态: " + orderStatus + "，需继续轮询", false);
        }
    }
}
