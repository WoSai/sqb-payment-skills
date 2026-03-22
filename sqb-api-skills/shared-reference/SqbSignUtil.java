package com.example.shouqianba.shared;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * 收钱吧签名工具类
 *
 * ⚠️ 重要：所有交易类 skill 共享此签名实现，不要自行编写签名逻辑。
 *
 * 签名算法：MD5(request_body + key)
 * - request_body 必须是 UTF-8 编码的原始 JSON 字符串
 * - 签名时的字符串必须和实际发送的请求体完全一致（包括字段顺序、空格等）
 * - MD5 输出为 32 位小写十六进制字符串
 * - Authorization 头格式：{sn} {sign}（sn 和 sign 之间有且仅有一个空格）
 */
public class SqbSignUtil {

    /**
     * 计算收钱吧 MD5 签名
     *
     * @param bodyStr 请求体的原始 JSON 字符串（UTF-8）
     * @param key     密钥（vendor_key 或 terminal_key）
     * @return 32 位小写十六进制 MD5 签名字符串
     */
    public static String md5Sign(String bodyStr, String key) {
        String signContent = bodyStr + key;
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] digest = md.digest(signContent.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(32);
            for (byte b : digest) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("MD5 algorithm not available", e);
        }
    }

    /**
     * 构建 Authorization 请求头值
     *
     * @param sn      序列号（vendor_sn 或 terminal_sn）
     * @param bodyStr 请求体 JSON 字符串
     * @param key     密钥（vendor_key 或 terminal_key）
     * @return Authorization 头的值，格式：{sn} {sign}
     */
    public static String buildAuthorization(String sn, String bodyStr, String key) {
        return sn + " " + md5Sign(bodyStr, key);
    }
}
