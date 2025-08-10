package com.mcp.myPayments.dto.response;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record TransactionResponse(
        Integer id,
        Integer customerId,
        BigDecimal amount,
        String currency,
        String category,
        String status,            // PENDING | COMPLETED | FAILED
        LocalDateTime createdAt,
        String description
) {}

