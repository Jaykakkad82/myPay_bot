package com.mcp.myPayments.mapper;

import com.mcp.myPayments.dto.request.CreateCustomerRequest;
import com.mcp.myPayments.dto.response.CustomerResponse;
import com.mcp.myPayments.model.Customer;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
public class CustomerMapper {

    public Customer toEntity(CreateCustomerRequest req) {
        if (req == null) return null;
        return Customer.builder()
                .fullName(req.fullName())
                .email(req.email())
                .phoneNumber(req.phoneNumber())
                .createdAt(LocalDateTime.now())
                .build();
    }

    public CustomerResponse toResponse(Customer c) {
        if (c == null) return null;
        return new CustomerResponse(
                c.getId(),
                c.getFullName(),
                c.getEmail(),
                c.getPhoneNumber()
        );
    }
}

