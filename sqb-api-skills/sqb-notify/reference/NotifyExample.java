package com.example.shouqianba;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * 收钱吧异步回调通知处理示例 (Spring Boot)
 *
 * 回调是对主动轮询的补充，不能完全替代主动查询
 * 必须做幂等处理和签名验证
 */
// @RestController
// @RequestMapping("/api/shouqianba")
public class NotifyExample {

    private static final ObjectMapper mapper = new ObjectMapper();

    // @Autowired
    // private OrderService orderService;  // 订单服务

    // @Autowired
    // private TerminalService terminalService;  // 终端服务（获取 terminal_key）

    /**
     * 接收收钱吧回调通知
     *
     * 配置方式：在支付请求中设置 notify_url 参数
     * 例如：notify_url = "https://your-domain.com/api/shouqianba/notify"
     */
    // @PostMapping("/notify")
    public String handleNotify(/* @RequestBody String body, @RequestHeader("Authorization") String auth */) {
        String body = "";  // 从请求中获取原始 body
        String auth = "";  // 从请求头获取 Authorization

        try {
            // 1. 验证签名
            if (!verifySignature(body, auth)) {
                System.err.println("回调签名验证失败，可能是伪造请求");
                return "FAIL";  // 返回非 200 会触发重试
            }

            // 2. 解析回调数据
            JsonNode data = mapper.readTree(body);
            String sn = data.path("sn").asText();
            String clientSn = data.path("client_sn").asText();
            String orderStatus = data.path("order_status").asText();
            String totalAmount = data.path("total_amount").asText();

            System.out.println("收到回调通知: sn=" + sn + ", status=" + orderStatus);

            // 3. 幂等处理：检查订单是否已处理
            // Order order = orderService.getByClientSn(clientSn);
            // if (order != null && order.isFinalStatus()) {
            //     // 已是最终状态，忽略重复回调
            //     return "200";
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

            // 5. 返回 200 表示接收成功
            return "200";

        } catch (Exception e) {
            System.err.println("处理回调异常: " + e.getMessage());
            return "FAIL";  // 返回非 200 触发重试
        }
    }

    /**
     * 验证回调签名
     *
     * @param body 原始请求体
     * @param auth Authorization 头内容
     * @return 签名是否合法
     */
    private boolean verifySignature(String body, String auth) {
        if (auth == null || !auth.contains(" ")) {
            return false;
        }

        String[] parts = auth.split(" ", 2);
        String terminalSn = parts[0];
        String receivedSign = parts[1];

        // 从存储中获取该终端的 terminal_key
        // String terminalKey = terminalService.getTerminalKey(terminalSn);
        String terminalKey = "your_terminal_key"; // 替换为真实逻辑

        if (terminalKey == null) {
            System.err.println("未找到终端: " + terminalSn);
            return false;
        }

        String expectedSign = md5(body + terminalKey);
        return expectedSign.equals(receivedSign);
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
