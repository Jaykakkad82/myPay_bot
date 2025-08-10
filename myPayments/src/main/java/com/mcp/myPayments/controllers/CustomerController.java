package com.mcp.myPayments.controllers;

import com.mcp.myPayments.dto.request.CreateCustomerRequest;
import com.mcp.myPayments.dto.response.CustomerResponse;
import com.mcp.myPayments.dto.response.TransactionResponse;
import com.mcp.myPayments.service.CustomerService;
import com.mcp.myPayments.service.TransactionService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.format.annotation.DateTimeFormat.ISO;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/v1/service/customers")
@RequiredArgsConstructor
public class CustomerController {

    private final CustomerService customerService;
    private final TransactionService transactionService;

    @PostMapping
    public ResponseEntity<CustomerResponse> create(@RequestBody @Valid CreateCustomerRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(customerService.create(req));
    }

    @GetMapping("/{id}")
    public ResponseEntity<CustomerResponse> get(@PathVariable Integer id) {
        return customerService.get(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    /** Customer transaction history + filters */
    @GetMapping("/{id}/transactions")
    public Page<TransactionResponse> listTransactions(
            @PathVariable Integer id,
            @RequestParam(required = false) String status,          // PENDING|COMPLETED|FAILED
            @RequestParam(required = false) String category,        // Retail, Subscription, etc.
            @RequestParam(required = false) String currency,        // USD|EUR|INR
            @RequestParam(required = false) @DateTimeFormat(iso = ISO.DATE_TIME) LocalDateTime from,
            @RequestParam(required = false) @DateTimeFormat(iso = ISO.DATE_TIME) LocalDateTime to,
            Pageable pageable
    ) {
        return transactionService.listForCustomer(id, status, category, currency, from, to, pageable);
    }
}

