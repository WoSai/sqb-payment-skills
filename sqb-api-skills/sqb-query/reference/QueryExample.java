package com.example.shouqianba;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * 收钱吧订单查询示例
 *
 * 支持单次查询和轮询查询两种模式
 */
public class QueryExample {

    private static final String API_BASE = "https://vsi-api.shouqianba.com";
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    private static final OkHttpClient client = new OkHttpClient();
    private static final ObjectMapper mapper = new ObjectMapper();

    // 最终状态集合
    private static final Set<String> FINAL_STATUSES = new HashSet<>(Arrays.asList(
        "PAID", "PAY_CANCELED", "REFUNDED", "PARTIAL_REFUNDED"
    ));

    private String terminalSn;
    private String terminalKey;

    public QueryExample(String terminalSn, String terminalKey) {
        this.terminalSn = terminalSn;
        this.terminalKey = terminalKey;
    }

    /**
     * 查询订单（通过商户订单号）
     */
    public QueryResult queryByClientSn(String clientSn) throws IOException {
        ObjectNode body = mapper.createObjectNode();
        body.put("terminal_sn", terminalSn);
        body.put("client_sn", clientSn);
        return doQuery(body);
    }

    /**
     * 查询订单（通过收钱吧订单号）
     */
    public QueryResult queryBySn(String sn) throws IOException {
        ObjectNode body = mapper.createObjectNode();
        body.put("terminal_sn", terminalSn);
        body.put("sn", sn);
        return doQuery(body);
    }

    /**
     * 轮询查询（等待最终状态）
     *
     * @param clientSn       商户订单号
     * @param maxWaitSeconds 最大等待时间
     * @return 最终查询结果
     */
    public QueryResult pollUntilFinal(String clientSn, int maxWaitSeconds)
            throws IOException, InterruptedException {

        long startTime = System.currentTimeMillis();

        while (true) {
            long elapsed = (System.currentTimeMillis() - startTime) / 1000;

            if (elapsed > maxWaitSeconds) {
                return new QueryResult("TIMEOUT", null, "轮询超时");
            }

            QueryResult result = queryByClientSn(clientSn);
            if (result.isFinal()) {
                return result;
            }

            System.out.println("[" + elapsed + "s] 状态: " + result.orderStatus + "，继续轮询...");

            // 轮询间隔：前60秒3秒，之后10秒
            int interval = elapsed < 60 ? 3 : 10;
            Thread.sleep(interval * 1000L);
        }
    }

    private QueryResult doQuery(ObjectNode body) throws IOException {
        String bodyStr = mapper.writeValueAsString(body);
        String sign = md5(bodyStr + terminalKey);

        Request request = new Request.Builder()
            .url(API_BASE + "/upay/v2/query")
            .addHeader("Authorization", terminalSn + " " + sign)
            .addHeader("Content-Type", "application/json; charset=utf-8")
            .post(RequestBody.create(bodyStr, JSON))
            .build();

        try (Response response = client.newCall(request).execute()) {
            String respBody = response.body().string();
            JsonNode resp = mapper.readTree(respBody);

            if (!"200".equals(resp.path("result_code").asText())) {
                return new QueryResult("ERROR", null,
                    resp.path("error_message").asText("通信失败"));
            }

            JsonNode bizResponse = resp.path("biz_response");
            if (!"SUCCESS".equals(bizResponse.path("result_code").asText())) {
                return new QueryResult("ERROR", null,
                    "查询失败: " + bizResponse.path("result_code").asText());
            }

            JsonNode data = bizResponse.path("data");
            return new QueryResult(
                data.path("order_status").asText(),
                data,
                "查询成功"
            );
        }
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
     * 查询结果
     */
    public static class QueryResult {
        public final String orderStatus;
        public final JsonNode data;
        public final String message;

        public QueryResult(String orderStatus, JsonNode data, String message) {
            this.orderStatus = orderStatus;
            this.data = data;
            this.message = message;
        }

        public boolean isFinal() {
            return FINAL_STATUSES.contains(orderStatus);
        }

        @Override
        public String toString() {
            return "QueryResult{orderStatus='" + orderStatus + "', message='" + message + "'}";
        }
    }
}
