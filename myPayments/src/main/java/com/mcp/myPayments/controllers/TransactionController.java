package com.mcp.myPayments.controllers;

import com.mcp.myPayments.dto.request.CreateTransactionRequest;
import com.mcp.myPayments.dto.response.PaymentResponse;
import com.mcp.myPayments.dto.response.TransactionResponse;
import com.mcp.myPayments.service.PaymentService;
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
@RequestMapping("/api/v1/service/transactions")
@RequiredArgsConstructor
public class TransactionController {

    private final TransactionService transactionService;
    private final PaymentService paymentService;

    @PostMapping
    public ResponseEntity<TransactionResponse> create(@RequestBody @Valid CreateTransactionRequest req,
                                                      @RequestHeader(value = "Idempotency-Key", required = false) String idemKey) {
        return ResponseEntity.status(HttpStatus.CREATED).body(transactionService.create(req, idemKey));
    }

    @GetMapping("/{id}")
    public ResponseEntity<TransactionResponse> get(@PathVariable Integer id) {
        return transactionService.get(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    /** Search / list with filters */
    @GetMapping
    public Page<TransactionResponse> search(
            @RequestParam(required = false) Integer customerId,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String currency,
            @RequestParam(required = false) @DateTimeFormat(iso = ISO.DATE_TIME) LocalDateTime from,
            @RequestParam(required = false) @DateTimeFormat(iso = ISO.DATE_TIME) LocalDateTime to,
            Pageable pageable
    ) {
        return transactionService.search(customerId, status, category, currency, from, to, pageable);
    }

    /** Convenience: find payment for a transaction */
    @GetMapping("/{id}/payment")
    public ResponseEntity<PaymentResponse> getPayment(@PathVariable Integer id) {
        return paymentService.getByTransactionId(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    /** Optional: cancel PENDING transaction */
    @PostMapping("/{id}/cancel")
    public ResponseEntity<TransactionResponse> cancel(@PathVariable Integer id,
                                                      @RequestHeader(value = "Idempotency-Key", required = false) String idemKey) {
        return ResponseEntity.ok(transactionService.cancel(id, idemKey));
    }
}
