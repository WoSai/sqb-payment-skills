package com.example.shouqianba;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * 收钱吧终端激活示例
 *
 * 使用 vendor_sn + vendor_key 签名（与交易接口不同）
 * 激活成功后获取 terminal_sn 和 terminal_key，用于后续交易签名
 */
public class ActivateExample {

    private static final String API_BASE = "https://vsi-api.shouqianba.com";
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    private static final OkHttpClient client = new OkHttpClient();
    private static final ObjectMapper mapper = new ObjectMapper();

    // 服务商凭证（替换为真实值）
    private static final String VENDOR_SN = "your_vendor_sn";
    private static final String VENDOR_KEY = "your_vendor_key";

    public static void main(String[] args) throws Exception {
        ActivateResult result = activate(
            "2019032019283301102",  // app_id
            "11000200",             // 激活码
            "DEVICE_001"            // 设备ID
        );

        if (result != null) {
            System.out.println("激活成功！");
            System.out.println("terminal_sn: " + result.terminalSn);
            System.out.println("terminal_key: " + result.terminalKey);
            // TODO: 将 terminal_sn 和 terminal_key 持久化存储
        }
    }

    /**
     * 终端激活
     *
     * @param appId    应用ID
     * @param code     激活码（一次性使用）
     * @param deviceId 设备唯一标识
     * @return 激活结果，包含 terminal_sn 和 terminal_key
     */
    public static ActivateResult activate(String appId, String code, String deviceId) throws IOException {
        // 1. 构建请求体
        ObjectNode body = mapper.createObjectNode();
        body.put("app_id", appId);
        body.put("code", code);
        body.put("device_id", deviceId);

        String bodyStr = mapper.writeValueAsString(body);

        // 2. 计算签名（vendor 级别签名）
        String sign = md5(bodyStr + VENDOR_KEY);

        // 3. 发送请求
        Request request = new Request.Builder()
            .url(API_BASE + "/terminal/activate")
            .addHeader("Authorization", VENDOR_SN + " " + sign)
            .addHeader("Content-Type", "application/json; charset=utf-8")
            .post(RequestBody.create(bodyStr, JSON))
            .build();

        try (Response response = client.newCall(request).execute()) {
            String respBody = response.body().string();
            JsonNode resp = mapper.readTree(respBody);

            // 4. 解析响应
            String resultCode = resp.get("result_code").asText();
            if (!"200".equals(resultCode)) {
                System.err.println("通信失败: " + resp.path("error_code").asText()
                    + " - " + resp.path("error_message").asText());
                return null;
            }

            JsonNode bizResponse = resp.get("biz_response");
            String bizResultCode = bizResponse.get("result_code").asText();
            if (!"ACTIVATE_SUCCESS".equals(bizResultCode)) {
                System.err.println("激活失败: " + bizResultCode
                    + " - " + bizResponse.path("error_message").asText());
                return null;
            }

            // 5. 提取凭证
            JsonNode data = bizResponse.get("data");
            return new ActivateResult(
                data.get("terminal_sn").asText(),
                data.get("terminal_key").asText()
            );
        }
    }

    /**
     * MD5 签名
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
     * 激活结果
     */
    public static class ActivateResult {
        public final String terminalSn;
        public final String terminalKey;

        public ActivateResult(String terminalSn, String terminalKey) {
            this.terminalSn = terminalSn;
            this.terminalKey = terminalKey;
        }
    }
}
