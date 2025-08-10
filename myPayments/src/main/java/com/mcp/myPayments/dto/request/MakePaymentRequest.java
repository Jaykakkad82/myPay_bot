package com.mcp.myPayments.dto.request;


import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record MakePaymentRequest(
        @NotNull Integer transactionId,
        @NotBlank String method       // e.g., CreditCard, UPI, NetBanking, Wallet
) {}

