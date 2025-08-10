package com.mcp.myPayments.dto.response;

public record CustomerResponse(
        Integer id,
        String fullName,
        String email,
        String phoneNumber
) {}
