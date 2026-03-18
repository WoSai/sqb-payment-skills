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
 * 收钱吧终端签到示例
 *
 * 签到会更新 terminal_key，必须持久化新 key
 * 建议每日首次交易前签到
 */
public class CheckinExample {

    private static final String API_BASE = "https://vsi-api.shouqianba.com";
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    private static final OkHttpClient client = new OkHttpClient();
    private static final ObjectMapper mapper = new ObjectMapper();

    /**
     * 终端签到
     *
     * @param terminalSn  终端序列号
     * @param terminalKey 当前终端密钥
     * @param deviceId    设备唯一标识
     * @return 新的 terminal_key，签到失败返回 null
     */
    public static String checkin(String terminalSn, String terminalKey, String deviceId)
            throws IOException {

        // 1. 构建请求体
        ObjectNode body = mapper.createObjectNode();
        body.put("terminal_sn", terminalSn);
        body.put("device_id", deviceId);

        String bodyStr = mapper.writeValueAsString(body);

        // 2. 计算签名（terminal 级别）
        String sign = md5(bodyStr + terminalKey);

        // 3. 发送请求
        Request request = new Request.Builder()
            .url(API_BASE + "/terminal/checkin")
            .addHeader("Authorization", terminalSn + " " + sign)
            .addHeader("Content-Type", "application/json; charset=utf-8")
            .post(RequestBody.create(bodyStr, JSON))
            .build();

        try (Response response = client.newCall(request).execute()) {
            String respBody = response.body().string();
            JsonNode resp = mapper.readTree(respBody);

            // 4. 解析响应
            String resultCode = resp.get("result_code").asText();
            if (!"200".equals(resultCode)) {
                System.err.println("签到通信失败: " + resp.path("error_code").asText()
                    + " - " + resp.path("error_message").asText());
                return null;
            }

            JsonNode bizResponse = resp.get("biz_response");
            String bizResultCode = bizResponse.get("result_code").asText();

            if (!"TERMINAL_CHECKIN_SUCCESS".equals(bizResultCode)) {
                System.err.println("签到失败: " + bizResultCode);
                // 签到失败可能意味着 key 已过期，需要重新激活
                System.err.println("如持续失败，请重新激活终端");
                return null;
            }

            // 5. 获取新的 terminal_key（关键！）
            JsonNode data = bizResponse.get("data");
            String newTerminalKey = data.get("terminal_key").asText();

            System.out.println("签到成功，新 terminal_key: " + newTerminalKey);
            return newTerminalKey;
        }
    }

    /**
     * 签到并更新持久化存储
     */
    public static void checkinAndUpdateKey(String terminalSn, String terminalKey,
            String deviceId) throws IOException {
        String newKey = checkin(terminalSn, terminalKey, deviceId);
        if (newKey != null) {
            // TODO: 更新持久化存储中的 terminal_key
            // db.update("UPDATE terminal SET terminal_key = ? WHERE terminal_sn = ?", newKey, terminalSn);
            // 集群部署时需确保所有节点同步更新
            System.out.println("terminal_key 已更新，请确保持久化存储已同步");
        } else {
            System.err.println("签到失败，保留旧 key 并建议重试或重新激活");
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
}
