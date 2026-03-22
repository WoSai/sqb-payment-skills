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
 * 收钱吧 C扫B 预下单支付示例
 *
 * 核心流程：预下单 → 获取二维码 → 顾客扫码 → 轮询查询 → 确认结果
 *
 * ⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易
 * 测试后务必通过退款接口进行退款清理
 */
public class PrecreateExample {

    private static final String API_BASE = "https://vsi-api.shouqianba.com";
    private static final MediaType JSON_TYPE = MediaType.get("application/json; charset=utf-8");
    private static final OkHttpClient client = new OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build();
    private static final ObjectMapper mapper = new ObjectMapper();

    // 轮询策略配置（对应 shared-reference/SqbPollingUtil 的 PRECREATE_POLLING_CONFIG）
    private static final int PHASE1_DURATION = 30;   // 第一阶段持续时间（秒）
    private static final int PHASE1_INTERVAL = 2;    // 第一阶段轮询间隔（秒）
    private static final int PHASE2_INTERVAL = 5;    // 第二阶段轮询间隔（秒）
    private static final int MAX_TIMEOUT = 240;      // 总超时时间（秒），预下单二维码约4分钟过期

    // 支付渠道
    public static final String PAYWAY_ALIPAY = "1";
    public static final String PAYWAY_WECHAT = "3";

    // 终端凭证（激活后获得，替换为真实值）
    private String terminalSn;
    private String terminalKey;

    public PrecreateExample(String terminalSn, String terminalKey) {
        this.terminalSn = terminalSn;
        this.terminalKey = terminalKey;
    }

    /**
     * C扫B 预下单
     *
     * @param clientSn    商户唯一订单号
     * @param totalAmount 金额（单位：分）
     * @param payway      支付方式（1=支付宝, 3=微信）— 预下单必填
     * @param subject     交易简介（显示在顾客账单）
     * @param operator    操作员
     * @return 预下单结果（包含 qr_code）
     */
    public PrecreateResult precreate(String clientSn, String totalAmount, String payway,
                                      String subject, String operator) throws IOException {

        // payway 必填校验
        if (payway == null || (!PAYWAY_ALIPAY.equals(payway) && !PAYWAY_WECHAT.equals(payway))) {
            throw new IllegalArgumentException("预下单必须指定 payway（1=支付宝, 3=微信）");
        }

        // 1. 构建请求体
        ObjectNode body = mapper.createObjectNode();
        body.put("terminal_sn", terminalSn);
        body.put("client_sn", clientSn);
        body.put("total_amount", totalAmount);
        body.put("payway", payway);
        body.put("subject", subject);
        body.put("operator", operator);

        String bodyStr = mapper.writeValueAsString(body);

        // 2. 计算签名（参考 shared-reference/SqbSignUtil）
        String sign = md5(bodyStr + terminalKey);

        // 3. 发送预下单请求
        Request request = new Request.Builder()
            .url(API_BASE + "/upay/v2/precreate")
            .addHeader("Authorization", terminalSn + " " + sign)
            .addHeader("Content-Type", "application/json; charset=utf-8")
            .post(RequestBody.create(bodyStr, JSON_TYPE))
            .build();

        try (Response response = client.newCall(request).execute()) {
            String respBody = response.body().string();
            JsonNode resp = mapper.readTree(respBody);

            // 4. 三层状态判定（参考 shared-reference/SqbStatusUtil）
            return parsePrecreateResponse(resp, clientSn);
        }
    }

    /**
     * 解析预下单响应（三层判定）
     */
    private PrecreateResult parsePrecreateResponse(JsonNode resp, String clientSn) {
        // 第一层：通信层
        String resultCode = resp.path("result_code").asText();
        if (!"200".equals(resultCode)) {
            return new PrecreateResult("FAIL", null, null,
                "通信失败: " + resp.path("error_message").asText());
        }

        JsonNode bizResponse = resp.path("biz_response");
        String bizResultCode = bizResponse.path("result_code").asText();

        // 第二层：业务层
        switch (bizResultCode) {
            case "PRECREATE_SUCCESS":
                break; // 继续判断第三层
            case "PRECREATE_FAIL":
                return new PrecreateResult("FAIL", null, null, "预下单失败");
            case "PRECREATE_IN_PROGRESS":
            case "PRECREATE_FAIL_ERROR":
                // 非最终状态，需要轮询
                return new PrecreateResult("PENDING", clientSn, null, "预下单处理中，需轮询查询");
            default:
                return new PrecreateResult("PENDING", clientSn, null, "未知业务状态: " + bizResultCode);
        }

        // 第三层：订单状态
        JsonNode data = bizResponse.path("data");
        String orderStatus = data.path("order_status").asText();
        String qrCode = data.path("qr_code").asText(null);

        switch (orderStatus) {
            case "PAID":
                return new PrecreateResult("SUCCESS", data.path("sn").asText(), null, "支付成功");
            case "PAY_CANCELED":
                return new PrecreateResult("FAIL", null, null, "支付已撤销");
            default:
                // IN_QUEUE, CREATED 等非最终状态 — 提取 qr_code 供前端渲染
                // ⚠️ 前端需要将 qr_code 字段渲染为二维码图片供顾客扫码
                return new PrecreateResult("PENDING", clientSn, qrCode,
                    "预下单成功，状态: " + orderStatus + "，请将 qr_code 渲染为二维码");
        }
    }

    /**
     * 带轮询的完整预下单支付流程
     *
     * 轮询策略（对应 shared-reference/SqbPollingUtil 的 PRECREATE_POLLING_CONFIG）：
     *   - 前 30 秒每 2 秒查询一次
     *   - 之后每 5 秒查询一次
     *   - 预下单订单约 4 分钟（240 秒）后自动过期
     */
    public PrecreateResult precreateWithPolling(String clientSn, String totalAmount, String payway,
                                                  String subject, String operator)
            throws IOException, InterruptedException {

        // 1. 发起预下单
        PrecreateResult result = precreate(clientSn, totalAmount, payway, subject, operator);

        // 2. 如果是最终状态，直接返回
        if (!"PENDING".equals(result.status)) {
            return result;
        }

        // 展示二维码信息
        if (result.qrCode != null) {
            System.out.println("二维码内容: " + result.qrCode);
            System.out.println("⚠️ 前端需要将 qr_code 渲染为二维码图片供顾客扫码");
        }

        // 3. 非最终状态，启动轮询（使用 PRECREATE_POLLING_CONFIG 策略）
        System.out.println("等待顾客扫码支付，启动轮询查询...");
        long startTime = System.currentTimeMillis();

        while (true) {
            long elapsed = (System.currentTimeMillis() - startTime) / 1000;

            // 超时退出
            if (elapsed > MAX_TIMEOUT) {
                System.err.println("轮询超时（" + MAX_TIMEOUT + "秒），预下单二维码已过期，请人工确认订单状态");
                return new PrecreateResult("TIMEOUT", clientSn, null, "轮询超时，二维码已过期");
            }

            // 轮询间隔：前30秒2秒，之后5秒
            int interval = elapsed < PHASE1_DURATION ? PHASE1_INTERVAL : PHASE2_INTERVAL;
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
                return new PrecreateResult("SUCCESS",
                    queryResult.path("biz_response").path("data").path("sn").asText(),
                    null, "支付成功");
            } else if ("PAY_CANCELED".equals(orderStatus)) {
                return new PrecreateResult("FAIL", null, null, "支付已撤销");
            }
            // 其他状态（IN_QUEUE, CREATED 等）继续轮询
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
     * 预下单结果
     */
    public static class PrecreateResult {
        public final String status;   // SUCCESS, FAIL, PENDING, TIMEOUT
        public final String orderSn;  // 收钱吧订单号或 client_sn
        public final String qrCode;   // 二维码内容（前端需渲染为二维码图片）
        public final String message;

        public PrecreateResult(String status, String orderSn, String qrCode, String message) {
            this.status = status;
            this.orderSn = orderSn;
            this.qrCode = qrCode;
            this.message = message;
        }

        @Override
        public String toString() {
            return "PrecreateResult{status='" + status + "', orderSn='" + orderSn
                + "', qrCode='" + qrCode + "', message='" + message + "'}";
        }
    }

    public static void main(String[] args) throws Exception {
        // ⚠️ 警告：收钱吧没有沙盒环境，此代码将发起真实交易
        // 测试后请务必通过退款接口清理测试订单

        PrecreateExample api = new PrecreateExample("your_terminal_sn", "your_terminal_key");

        // 生成唯一订单号
        String clientSn = generateClientSn("STORE01");

        // 发起预下单（带轮询）
        // 注意：这是真实交易！测试后请务必退款
        PrecreateResult result = api.precreateWithPolling(
            clientSn,
            "1",              // 1分钱（测试用）
            PAYWAY_WECHAT,    // 微信支付（3）
            "测试商品",        // 账单显示
            "cashier_01"      // 操作员
        );

        System.out.println("支付结果: " + result);

        // ⚠️ 测试完成后，请使用退款接口退款：
        // POST /upay/v2/refund
        // 参考 sqb-refund skill
    }
}
