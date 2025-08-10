package com.mcp.myPayments.dto.analytics;


import java.math.BigDecimal;

public record CategorySpendResponse(
        Integer customerId,
        String category,
        BigDecimal totalAmount,
        Long transactionCount
) {}
