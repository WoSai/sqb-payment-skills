package com.example.shouqianba;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

/**
 * 收钱吧回调 RSA 验签工具
 *
 * ⚠️ 重要：验签是防止资金损失的最后一道防线，不可省略。
 *
 * 验签算法：RSA SHA256WithRSA（非对称签名，非 MD5）
 * Authorization 头格式（回调场景）：{terminal_sn} {base64_encoded_signature}
 *
 * 验签流程：
 * 1. 从 Authorization header 提取 terminal_sn 和 Base64 编码的签名
 * 2. 使用收钱吧 RSA 公钥 + SHA256WithRSA 算法验证
 * 3. 验证对象是 HTTP body 的原始字节流
 * 4. 验证失败立即返回 403
 */
public class CallbackVerifyExample {

    // 收钱吧 RSA 公钥（从服务商平台获取，安全存储于配置或 KMS）
    private static volatile PublicKey sqbPublicKey;

    /**
     * 加载收钱吧 RSA 公钥
     *
     * 公钥来源：从收钱吧服务商平台获取。
     * 建议使用配置文件或密钥管理服务（KMS / Vault）安全存储。
     */
    public static PublicKey loadSqbPublicKey() throws Exception {
        if (sqbPublicKey != null) {
            return sqbPublicKey;
        }
        synchronized (CallbackVerifyExample.class) {
            if (sqbPublicKey != null) {
                return sqbPublicKey;
            }
            // 从文件加载 PEM 格式公钥
            String pemPath = System.getProperty("sqb.public.key.path", "sqb_public_key.pem");
            String pem = new String(Files.readAllBytes(Paths.get(pemPath)), StandardCharsets.UTF_8);
            String base64Key = pem
                .replace("-----BEGIN PUBLIC KEY-----", "")
                .replace("-----END PUBLIC KEY-----", "")
                .replaceAll("\\s+", "");
            byte[] keyBytes = Base64.getDecoder().decode(base64Key);
            X509EncodedKeySpec spec = new X509EncodedKeySpec(keyBytes);
            sqbPublicKey = KeyFactory.getInstance("RSA").generatePublic(spec);
            return sqbPublicKey;
        }
    }

    /**
     * RSA SHA256WithRSA 回调验签
     *
     * @param bodyBytes 原始请求体字节流
     * @param auth      Authorization 头内容，格式：{terminal_sn} {base64_signature}
     * @return 验签是否通过
     */
    public static boolean verifySignatureRsa(byte[] bodyBytes, String auth) {
        if (auth == null || !auth.contains(" ")) {
            return false;
        }

        String[] parts = auth.split(" ", 2);
        String terminalSn = parts[0];
        String receivedSignB64 = parts[1];

        try {
            byte[] signatureBytes = Base64.getDecoder().decode(receivedSignB64);
            PublicKey publicKey = loadSqbPublicKey();

            Signature signature = Signature.getInstance("SHA256WithRSA");
            signature.initVerify(publicKey);
            signature.update(bodyBytes);

            return signature.verify(signatureBytes);
        } catch (Exception e) {
            System.err.println("RSA 验签失败 [terminal_sn=" + terminalSn + "]: " + e.getMessage());
            return false;
        }
    }
}
