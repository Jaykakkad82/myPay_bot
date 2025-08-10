package com.mcp.myPayments.dto.response;


import java.time.LocalDateTime;

public record PaymentResponse(
        Integer id,
        Integer transactionId,
        String method,            // CreditCard | UPI | ...
        String status,            // INITIATED | SUCCESS | FAILED
        String referenceId,
        LocalDateTime processedAt,
        String failureReason      // optional; null when success
) {}
