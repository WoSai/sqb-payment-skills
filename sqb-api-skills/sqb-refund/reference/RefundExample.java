package com.example.shouqianba;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.UUID;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * 收钱吧退款示例
 *
 * 支持全额退款和部分退款
 * 退款是异步操作，需查询确认最终结果
 * 注意：所有交易都是真实的，测试支付后务必退款
 */
public class RefundExample {

    private static final String API_BASE = "https://vsi-api.shouqianba.com";
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    private static final OkHttpClient client = new OkHttpClient();
    private static final ObjectMapper mapper = new ObjectMapper();

    private String terminalSn;
    private String terminalKey;

    public RefundExample(String terminalSn, String terminalKey) {
        this.terminalSn = terminalSn;
        this.terminalKey = terminalKey;
    }

    /**
     * 退款
     *
     * @param sn              收钱吧订单号（与 clientSn 二选一）
     * @param clientSn        商户订单号（与 sn 二选一）
     * @param refundRequestNo 退款请求号（商户系统内唯一）
     * @param refundAmount    退款金额（分）
     * @param operator        操作员
     * @param refundReason    退款原因（可选）
     * @return 退款结果
     */
    public RefundResult refund(String sn, String clientSn, String refundRequestNo,
                                String refundAmount, String operator, String refundReason)
            throws IOException {

        // 1. 构建请求体
        ObjectNode body = mapper.createObjectNode();
        body.put("terminal_sn", terminalSn);
        if (sn != null) body.put("sn", sn);
        if (clientSn != null) body.put("client_sn", clientSn);
        body.put("refund_request_no", refundRequestNo);
        body.put("refund_amount", refundAmount);
        body.put("operator", operator);
        if (refundReason != null) body.put("refund_reason", refundReason);

        String bodyStr = mapper.writeValueAsString(body);

        // 2. 计算签名
        String sign = md5(bodyStr + terminalKey);

        // 3. 发送退款请求
        Request request = new Request.Builder()
            .url(API_BASE + "/api/v2/refund")
            .addHeader("Authorization", terminalSn + " " + sign)
            .addHeader("Content-Type", "application/json; charset=utf-8")
            .post(RequestBody.create(bodyStr, JSON))
            .build();

        try (Response response = client.newCall(request).execute()) {
            String respBody = response.body().string();
            JsonNode resp = mapper.readTree(respBody);

            return parseRefundResponse(resp);
        }
    }

    private RefundResult parseRefundResponse(JsonNode resp) {
        // 第一层：通信层
        if (!"200".equals(resp.path("result_code").asText())) {
            return new RefundResult("FAIL", null,
                "通信失败: " + resp.path("error_message").asText());
        }

        JsonNode bizResponse = resp.path("biz_response");
        String bizResultCode = bizResponse.path("result_code").asText();

        // 第二层：业务层
        switch (bizResultCode) {
            case "REFUND_SUCCESS":
                JsonNode data = bizResponse.path("data");
                String orderStatus = data.path("order_status").asText();
                return new RefundResult(
                    "SUCCESS", data,
                    "退款成功，订单状态: " + orderStatus
                );

            case "REFUND_FAIL":
                return new RefundResult("FAIL", null,
                    "退款失败: " + bizResponse.path("error_message").asText());

            case "REFUND_IN_PROGRESS":
            case "REFUND_FAIL_ERROR":
                return new RefundResult("PENDING", null,
                    "退款处理中，请查询确认");

            default:
                return new RefundResult("FAIL", null,
                    "未知状态: " + bizResultCode);
        }
    }

    /**
     * 生成唯一退款请求号
     */
    public static String generateRefundRequestNo() {
        return "REF" + System.currentTimeMillis() + UUID.randomUUID().toString().substring(0, 4);
    }

    private static String md5(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] digest = md.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * 退款结果
     */
    public static class RefundResult {
        public final String status;   // SUCCESS, FAIL, PENDING
        public final JsonNode data;
        public final String message;

        public RefundResult(String status, JsonNode data, String message) {
            this.status = status;
            this.data = data;
            this.message = message;
        }

        @Override
        public String toString() {
            return "RefundResult{status='" + status + "', message='" + message + "'}";
        }
    }

    public static void main(String[] args) throws Exception {
        RefundExample refundApi = new RefundExample("your_terminal_sn", "your_terminal_key");

        // 全额退款示例
        String refundRequestNo = generateRefundRequestNo();
        RefundResult result = refundApi.refund(
            "7892840250140845",  // 收钱吧订单号
            null,                // 或使用 client_sn
            refundRequestNo,
            "100",               // 退款金额（分）
            "cashier_01",
            "顾客要求退款"
        );

        System.out.println("退款结果: " + result);

        // 如果退款处理中，需查询确认
        if ("PENDING".equals(result.status)) {
            System.out.println("退款处理中，请使用查询接口确认最终结果");
        }
    }
}
