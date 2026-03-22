package com.example.shouqianba;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
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
 * 收钱吧撤单（冲正）示例
 *
 * ⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易
 * 撤单操作不可逆，请谨慎使用！
 *
 * 核心流程：撤单 → 判定结果 → 失败则查询确认
 * 限制：仅限当天订单（当日 00:00 后的交易），全额撤销，已部分退款的订单不能撤单
 */
public class CancelExample {

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

    public CancelExample(String terminalSn, String terminalKey) {
        this.terminalSn = terminalSn;
        this.terminalKey = terminalKey;
    }

    /**
     * 撤单（冲正）
     *
     * ⚠️ 警告：此操作将发起真实撤单，不可逆！
     * ⚠️ 仅限当天订单（当日 00:00 后的交易），全额撤销
     * ⚠️ 已部分退款的订单不能撤单
     *
     * @param sn       收钱吧订单号（sn 和 clientSn 二选一，推荐优先使用 sn）
     * @param clientSn 商户订单号（sn 和 clientSn 二选一）
     * @return 撤单结果
     */
    public CancelResult cancel(String sn, String clientSn) throws IOException {
        if (sn == null && clientSn == null) {
            throw new IllegalArgumentException("sn 和 clientSn 必须至少提供一个");
        }

        // 1. 构建请求体
        ObjectNode body = mapper.createObjectNode();
        body.put("terminal_sn", terminalSn);
        if (sn != null) {
            body.put("sn", sn);
        }
        if (clientSn != null) {
            body.put("client_sn", clientSn);
        }

        String bodyStr = mapper.writeValueAsString(body);

        // 2. 计算签名（签名逻辑参考 shared-reference/SqbSignUtil）
        String sign = md5(bodyStr + terminalKey);

        // 3. 发送撤单请求
        Request request = new Request.Builder()
            .url(API_BASE + "/upay/v2/cancel")
            .addHeader("Authorization", terminalSn + " " + sign)
            .addHeader("Content-Type", "application/json; charset=utf-8")
            .post(RequestBody.create(bodyStr, JSON_TYPE))
            .build();

        try (Response response = client.newCall(request).execute()) {
            String respBody = response.body().string();
            JsonNode resp = mapper.readTree(respBody);

            // 4. 撤单结果判定
            return parseCancelResponse(resp);
        }
    }

    /**
     * 解析撤单响应
     *
     * 业务结果码：
     * - CANCEL_SUCCESS: 撤销成功
     * - CANCEL_ERROR: 撤销失败（不确定），需查询确认
     * - CANCEL_ABORT_SUCCESS: 中断支付成功
     * - CANCEL_ABORT_ERROR: 中断支付失败，需查询确认
     */
    private CancelResult parseCancelResponse(JsonNode resp) {
        // 第一层：通信层
        String resultCode = resp.path("result_code").asText();
        if (!"200".equals(resultCode)) {
            return new CancelResult("FAIL", null,
                "通信失败: " + resp.path("error_message").asText());
        }

        JsonNode bizResponse = resp.path("biz_response");
        String bizResultCode = bizResponse.path("result_code").asText();
        JsonNode data = bizResponse.path("data");

        // 第二层：业务层 — 撤单结果判定
        switch (bizResultCode) {
            case "CANCEL_SUCCESS":
                return new CancelResult("SUCCESS",
                    data.path("sn").asText(),
                    "撤单成功，交易已撤销，资金已退回");

            case "CANCEL_ABORT_SUCCESS":
                return new CancelResult("SUCCESS",
                    data.path("sn").asText(),
                    "中断支付成功，支付中的订单已被中断");

            case "CANCEL_ERROR":
                // ⚠️ 不确定状态，必须查询确认！
                return new CancelResult("UNCERTAIN",
                    data.isMissingNode() ? null : data.path("sn").asText(),
                    "撤单结果不确定（CANCEL_ERROR），必须调用查询接口确认订单最终状态");

            case "CANCEL_ABORT_ERROR":
                // ⚠️ 不确定状态，必须查询确认！
                return new CancelResult("UNCERTAIN",
                    data.isMissingNode() ? null : data.path("sn").asText(),
                    "中断支付结果不确定（CANCEL_ABORT_ERROR），必须调用查询接口确认订单最终状态");

            default:
                return new CancelResult("FAIL", null,
                    "撤单失败: " + bizResponse.path("error_message").asText(bizResultCode));
        }
    }

    /**
     * 查询订单状态（用于撤单结果不确定时确认）
     */
    private JsonNode queryOrder(String sn, String clientSn) throws IOException {
        ObjectNode body = mapper.createObjectNode();
        body.put("terminal_sn", terminalSn);
        if (sn != null) {
            body.put("sn", sn);
        } else if (clientSn != null) {
            body.put("client_sn", clientSn);
        }

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
     * 带查询确认的完整撤单流程
     *
     * ⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易
     *
     * 流程：
     * 1. 发起撤单请求
     * 2. 若撤单成功（CANCEL_SUCCESS / CANCEL_ABORT_SUCCESS），直接返回
     * 3. 若撤单结果不确定（CANCEL_ERROR / CANCEL_ABORT_ERROR），查询订单确认
     * 4. 查询确认订单最终状态
     *
     * @param sn              收钱吧订单号（sn 和 clientSn 二选一）
     * @param clientSn        商户订单号（sn 和 clientSn 二选一）
     * @param maxQueryAttempts 最大查询次数，默认 6 次
     * @param queryIntervalMs 查询间隔（毫秒），默认 5000ms
     * @return 撤单结果
     */
    public CancelResult cancelWithRetry(String sn, String clientSn,
                                         int maxQueryAttempts, long queryIntervalMs)
            throws IOException, InterruptedException {

        // 1. 发起撤单
        System.out.println("发起撤单请求...");
        CancelResult cancelResult = cancel(sn, clientSn);

        // 2. 撤单成功，直接返回
        if ("SUCCESS".equals(cancelResult.status)) {
            System.out.println("撤单成功: " + cancelResult.message);
            return cancelResult;
        }

        // 3. 撤单明确失败，直接返回
        if ("FAIL".equals(cancelResult.status)) {
            System.out.println("撤单失败: " + cancelResult.message);
            return cancelResult;
        }

        // 4. 撤单结果不确定（CANCEL_ERROR / CANCEL_ABORT_ERROR），启动查询确认
        System.out.println("撤单结果不确定: " + cancelResult.message);
        System.out.println("启动查询确认流程...");

        for (int attempt = 1; attempt <= maxQueryAttempts; attempt++) {
            Thread.sleep(queryIntervalMs);

            System.out.println("[第 " + attempt + "/" + maxQueryAttempts + " 次查询]");

            JsonNode queryResult;
            try {
                queryResult = queryOrder(sn, clientSn);
            } catch (IOException e) {
                System.err.println("查询异常: " + e.getMessage() + "，继续重试...");
                continue;
            }

            if (queryResult == null || !"200".equals(queryResult.path("result_code").asText())) {
                System.err.println("查询通信失败，继续重试...");
                continue;
            }

            String orderStatus = queryResult.path("biz_response")
                .path("data").path("order_status").asText();
            System.out.println("订单状态: " + orderStatus);

            // 判断最终状态
            if ("PAY_CANCELED".equals(orderStatus)) {
                String orderSn = queryResult.path("biz_response")
                    .path("data").path("sn").asText();
                return new CancelResult("SUCCESS", orderSn,
                    "查询确认：撤单已生效，订单已取消");
            } else if ("PAID".equals(orderStatus)) {
                String orderSn = queryResult.path("biz_response")
                    .path("data").path("sn").asText();
                return new CancelResult("FAIL", orderSn,
                    "查询确认：撤单未生效，订单仍为已支付状态（可重新发起撤单或退款）");
            }
            // 其他状态继续查询
        }

        // 查询多次仍无法确认
        System.err.println("查询 " + maxQueryAttempts + " 次后仍无法确认订单状态，建议人工介入处理");
        return new CancelResult("UNCERTAIN", cancelResult.orderSn,
            "查询 " + maxQueryAttempts + " 次后仍无法确认订单最终状态，建议人工介入处理");
    }

    /**
     * 带查询确认的完整撤单流程（使用默认查询参数）
     */
    public CancelResult cancelWithRetry(String sn, String clientSn)
            throws IOException, InterruptedException {
        return cancelWithRetry(sn, clientSn, 6, 5000L);
    }

    /**
     * MD5 签名计算（签名逻辑参考 shared-reference/SqbSignUtil）
     */
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
     * 撤单结果
     */
    public static class CancelResult {
        public final String status;   // SUCCESS, FAIL, UNCERTAIN
        public final String orderSn;  // 收钱吧订单号
        public final String message;

        public CancelResult(String status, String orderSn, String message) {
            this.status = status;
            this.orderSn = orderSn;
            this.message = message;
        }

        @Override
        public String toString() {
            return "CancelResult{status='" + status + "', orderSn='" + orderSn
                + "', message='" + message + "'}";
        }
    }

    public static void main(String[] args) throws Exception {
        // ⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易！
        // ⚠️ 仅限当天订单（当日 00:00 后的交易）
        // ⚠️ 撤单为全额撤销，已部分退款的订单不能撤单

        CancelExample cancelApi = new CancelExample("your_terminal_sn", "your_terminal_key");

        // 场景1：使用收钱吧订单号撤单（推荐）
        CancelResult result = cancelApi.cancelWithRetry("7892840250140845", null);
        System.out.println("撤单结果: " + result);

        // 场景2：使用商户订单号撤单
        // CancelResult result2 = cancelApi.cancelWithRetry(null, "20230615143052001");
        // System.out.println("撤单结果: " + result2);

        // 场景3：pay 接口超时后立即撤单保障资金安全
        // String payClientSn = "ORDER_THAT_TIMED_OUT";
        // CancelResult result3 = cancelApi.cancelWithRetry(null, payClientSn);
        // if ("SUCCESS".equals(result3.status)) {
        //     System.out.println("撤单成功，资金安全");
        // } else if ("FAIL".equals(result3.status)) {
        //     System.out.println("撤单失败，订单仍为已支付状态，请确认是否需要退款");
        // } else {
        //     System.out.println("撤单状态不确定，请人工确认");
        // }
    }
}
