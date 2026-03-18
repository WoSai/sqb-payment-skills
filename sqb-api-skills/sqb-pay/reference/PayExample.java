package com.example.shouqianba;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.TimeUnit;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * 收钱吧 B扫C 付款码支付示例
 *
 * 核心流程：扫码 → 支付 → 轮询查询 → 确认结果
 * 注意：所有交易都是真实的（无沙盒环境），测试后务必退款
 */
public class PayExample {

    private static final String API_BASE = "https://vsi-api.shouqianba.com";
    private static final MediaType JSON_TYPE = MediaType.get("application/json; charset=utf-8");
    private static final OkHttpClient client = new OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build();
    private static final ObjectMapper mapper = new ObjectMapper();

    // 终端凭证（激活后获得，替换为真实值）
    private String terminalSn;
    private String terminalKey;

    public PayExample(String terminalSn, String terminalKey) {
        this.terminalSn = terminalSn;
        this.terminalKey = terminalKey;
    }

    /**
     * 付款码支付
     *
     * @param clientSn   商户唯一订单号
     * @param totalAmount 金额（单位：分）
     * @param dynamicId  顾客付款码内容（扫码枪获取）
     * @param subject    交易简介（显示在顾客账单）
     * @param operator   操作员
     * @return 支付结果
     */
    public PayResult pay(String clientSn, String totalAmount, String dynamicId,
                         String subject, String operator) throws IOException {

        // 1. 构建请求体
        ObjectNode body = mapper.createObjectNode();
        body.put("terminal_sn", terminalSn);
        body.put("client_sn", clientSn);
        body.put("total_amount", totalAmount);
        body.put("dynamic_id", dynamicId);
        body.put("subject", subject);
        body.put("operator", operator);

        String bodyStr = mapper.writeValueAsString(body);

        // 2. 计算签名
        String sign = md5(bodyStr + terminalKey);

        // 3. 发送支付请求
        Request request = new Request.Builder()
            .url(API_BASE + "/upay/v2/pay")
            .addHeader("Authorization", terminalSn + " " + sign)
            .addHeader("Content-Type", "application/json; charset=utf-8")
            .post(RequestBody.create(bodyStr, JSON_TYPE))
            .build();

        try (Response response = client.newCall(request).execute()) {
            String respBody = response.body().string();
            JsonNode resp = mapper.readTree(respBody);

            // 4. 三层状态判定
            return parsePayResponse(resp, clientSn);
        }
    }

    /**
     * 解析支付响应（三层判定）
     */
    private PayResult parsePayResponse(JsonNode resp, String clientSn) {
        // 第一层：通信层
        String resultCode = resp.path("result_code").asText();
        if (!"200".equals(resultCode)) {
            return new PayResult("FAIL", null,
                "通信失败: " + resp.path("error_message").asText());
        }

        JsonNode bizResponse = resp.path("biz_response");
        String bizResultCode = bizResponse.path("result_code").asText();

        // 第二层：业务层
        switch (bizResultCode) {
            case "PAY_SUCCESS":
                break; // 继续判断第三层
            case "PAY_FAIL":
                return new PayResult("FAIL", null, "支付失败");
            case "PAY_IN_PROGRESS":
            case "PAY_FAIL_ERROR":
                // 非最终状态，需要轮询
                return new PayResult("PENDING", clientSn, "支付处理中，需轮询查询");
            default:
                return new PayResult("PENDING", clientSn, "未知业务状态: " + bizResultCode);
        }

        // 第三层：订单状态
        JsonNode data = bizResponse.path("data");
        String orderStatus = data.path("order_status").asText();

        switch (orderStatus) {
            case "PAID":
                return new PayResult("SUCCESS", data.path("sn").asText(), "支付成功");
            case "PAY_CANCELED":
                return new PayResult("FAIL", null, "支付已撤销");
            default:
                // CREATED, PAY_ERROR 等非最终状态
                return new PayResult("PENDING", clientSn, "状态: " + orderStatus + "，需轮询");
        }
    }

    /**
     * 带轮询的完整支付流程
     */
    public PayResult payWithPolling(String clientSn, String totalAmount, String dynamicId,
                                     String subject, String operator) throws IOException, InterruptedException {
        // 1. 发起支付
        PayResult result = pay(clientSn, totalAmount, dynamicId, subject, operator);

        // 2. 如果是最终状态，直接返回
        if (!"PENDING".equals(result.status)) {
            return result;
        }

        // 3. 非最终状态，启动轮询
        System.out.println("支付处理中，启动轮询查询...");
        long startTime = System.currentTimeMillis();
        int maxWaitSeconds = 120;

        while (true) {
            long elapsed = (System.currentTimeMillis() - startTime) / 1000;

            // 超时退出
            if (elapsed > maxWaitSeconds) {
                System.err.println("轮询超时（" + maxWaitSeconds + "秒），请人工确认订单状态");
                return new PayResult("TIMEOUT", clientSn, "轮询超时");
            }

            // 轮询间隔：前60秒3秒，之后10秒
            int interval = elapsed < 60 ? 3 : 10;
            Thread.sleep(interval * 1000L);

            // 查询订单
            JsonNode queryResult = queryOrder(clientSn);
            if (queryResult == null) {
                continue; // 查询失败，继续重试
            }

            String orderStatus = queryResult.path("biz_response")
                .path("data").path("order_status").asText();

            System.out.println("[" + elapsed + "s] 订单状态: " + orderStatus);

            // 判断最终状态
            if ("PAID".equals(orderStatus)) {
                return new PayResult("SUCCESS",
                    queryResult.path("biz_response").path("data").path("sn").asText(),
                    "支付成功");
            } else if ("PAY_CANCELED".equals(orderStatus)) {
                return new PayResult("FAIL", null, "支付已撤销");
            }
            // 其他状态继续轮询
        }
    }

    /**
     * 查询订单（用于轮询）
     */
    private JsonNode queryOrder(String clientSn) throws IOException {
        ObjectNode body = mapper.createObjectNode();
        body.put("terminal_sn", terminalSn);
        body.put("client_sn", clientSn);

        String bodyStr = mapper.writeValueAsString(body);
        String sign = md5(bodyStr + terminalKey);

        Request request = new Request.Builder()
            .url(API_BASE + "/upay/v2/query")
            .addHeader("Authorization", terminalSn + " " + sign)
            .addHeader("Content-Type", "application/json; charset=utf-8")
            .post(RequestBody.create(bodyStr, JSON_TYPE))
            .build();

        try (Response response = client.newCall(request).execute()) {
            return mapper.readTree(response.body().string());
        }
    }

    /**
     * 生成唯一订单号
     */
    public static String generateClientSn(String storeId) {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmssSSS"));
        return storeId + timestamp + String.format("%04d", (int) (Math.random() * 10000));
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
     * 支付结果
     */
    public static class PayResult {
        public final String status;   // SUCCESS, FAIL, PENDING, TIMEOUT
        public final String orderSn;  // 收钱吧订单号或 client_sn
        public final String message;

        public PayResult(String status, String orderSn, String message) {
            this.status = status;
            this.orderSn = orderSn;
            this.message = message;
        }

        @Override
        public String toString() {
            return "PayResult{status='" + status + "', orderSn='" + orderSn
                + "', message='" + message + "'}";
        }
    }

    public static void main(String[] args) throws Exception {
        PayExample payApi = new PayExample("your_terminal_sn", "your_terminal_key");

        // 生成唯一订单号
        String clientSn = generateClientSn("STORE01");

        // 发起支付（带轮询）
        // 注意：这是真实交易！测试后请务必退款
        PayResult result = payApi.payWithPolling(
            clientSn,
            "1",                     // 1分钱（测试用）
            "130818341921600584",     // 付款码（扫码枪获取）
            "测试商品",               // 账单显示
            "cashier_01"             // 操作员
        );

        System.out.println("支付结果: " + result);
    }
}
