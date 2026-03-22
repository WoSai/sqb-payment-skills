package com.example.shouqianba;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * 收钱吧异步回调通知处理示例 (Spring Boot)
 *
 * ⚠️ 警告：收钱吧没有沙盒环境，此代码处理的是真实交易回调。
 * 回调是对主动轮询的补充，不能完全替代主动查询。
 * 必须做幂等处理和 RSA 签名验证——验签是防止资金损失的最后一道防线。
 */
// @RestController
// @RequestMapping("/api/shouqianba")
public class NotifyExample {

    private static final ObjectMapper mapper = new ObjectMapper();

    // 收钱吧 RSA 公钥（从服务商平台获取，安全存储于配置或 KMS）
    private static volatile PublicKey sqbPublicKey;

    // @Autowired
    // private OrderService orderService;  // 订单服务

    /**
     * 加载收钱吧 RSA 公钥
     *
     * 公钥来源：从收钱吧服务商平台获取。
     * 建议使用配置文件或密钥管理服务（KMS / Vault）安全存储。
     */
    private static PublicKey loadSqbPublicKey() throws Exception {
        if (sqbPublicKey != null) {
            return sqbPublicKey;
        }
        synchronized (NotifyExample.class) {
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
     * 验签流程：
     * 1. 从 Authorization header 提取 terminal_sn 和 Base64 编码的签名
     * 2. 使用收钱吧 RSA 公钥 + SHA256WithRSA 算法验证签名
     * 3. 验签失败返回 false
     *
     * @param bodyBytes 原始请求体字节流
     * @param auth      Authorization 头内容
     * @return 验签是否通过
     */
    private boolean verifySignatureRsa(byte[] bodyBytes, String auth) {
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

    /**
     * 接收收钱吧回调通知
     *
     * 配置方式：在支付请求中设置 notify_url 参数
     * 例如：notify_url = "https://your-domain.com/api/shouqianba/notify"
     */
    // @PostMapping("/notify")
    public String handleNotify(/* @RequestBody byte[] bodyBytes, @RequestHeader("Authorization") String auth */) {
        byte[] bodyBytes = new byte[0];  // 从请求中获取原始 body 字节流
        String auth = "";  // 从请求头获取 Authorization

        try {
            // 1. RSA 验签（安全关键，不可跳过）
            if (!verifySignatureRsa(bodyBytes, auth)) {
                System.err.println("⚠️ 回调签名验证失败，拒绝处理——可能是伪造请求");
                // return ResponseEntity.status(403).body("FAIL");
                return "FAIL";
            }

            // 2. 解析回调数据
            JsonNode data = mapper.readTree(bodyBytes);
            String sn = data.path("sn").asText();
            String clientSn = data.path("client_sn").asText();
            String orderStatus = data.path("order_status").asText();
            String totalAmount = data.path("total_amount").asText();

            System.out.println("收到回调通知: sn=" + sn + ", status=" + orderStatus);

            // 3. 幂等处理：检查订单是否已处理
            // Order order = orderService.getByClientSn(clientSn);
            // if (order != null && order.isFinalStatus()) {
            //     // 已是最终状态，忽略重复回调
            //     return "success";
            // }

            // 4. 根据状态更新订单
            switch (orderStatus) {
                case "PAID":
                    // orderService.markAsPaid(clientSn, sn, totalAmount);
                    System.out.println("订单支付成功: " + clientSn);
                    break;
                case "PAY_CANCELED":
                    // orderService.markAsCanceled(clientSn);
                    System.out.println("订单支付取消: " + clientSn);
                    break;
                case "REFUNDED":
                    // orderService.markAsRefunded(clientSn);
                    System.out.println("订单已全额退款: " + clientSn);
                    break;
                case "PARTIAL_REFUNDED":
                    String refundedAmount = data.path("refunded_amount").asText();
                    // orderService.markAsPartialRefunded(clientSn, refundedAmount);
                    System.out.println("订单已部分退款: " + clientSn + ", 退款额: " + refundedAmount);
                    break;
                default:
                    System.out.println("收到非最终状态回调: " + orderStatus);
                    break;
            }

            // 5. 返回 success 表示接收成功
            return "success";

        } catch (Exception e) {
            System.err.println("处理回调异常: " + e.getMessage());
            return "FAIL";
        }
    }
}
