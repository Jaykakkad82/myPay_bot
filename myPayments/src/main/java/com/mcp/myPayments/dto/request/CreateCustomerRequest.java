package com.mcp.myPayments.dto.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateCustomerRequest(
        @NotBlank String fullName,
        @Email @NotBlank String email,
        @Size(max = 15) String phoneNumber
) {}
