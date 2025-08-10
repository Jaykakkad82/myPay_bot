package com.mcp.myPayments.dto.analytics;

import java.math.BigDecimal;

public record SpendSummaryResponse(
        Integer customerId,
        String baseCurrency,          // e.g., USD (if you normalize)
        BigDecimal totalAmount,
        Long transactionCount,
        BigDecimal averageTicket,
        String periodFrom,            // ISO-8601 strings for simplicity
        String periodTo
) {}

