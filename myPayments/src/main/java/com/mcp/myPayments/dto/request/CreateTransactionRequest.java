package com.mcp.myPayments.dto.request;


import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

public record CreateTransactionRequest(
        @NotNull Integer customerId,
        @NotNull @Min(0) BigDecimal amount,
        @NotBlank String currency,     // e.g., USD, EUR, INR
        @NotBlank String category,     // e.g., Retail, Subscription
        String description
) {}
