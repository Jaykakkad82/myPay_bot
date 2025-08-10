package com.mcp.myPayments.controllers;

import com.mcp.myPayments.dto.request.MakePaymentRequest;
import com.mcp.myPayments.dto.response.PaymentResponse;
import com.mcp.myPayments.service.PaymentService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.Optional;

@RestController
@RequestMapping("/api/v1/service/payments")
@RequiredArgsConstructor
public class PaymentController {

    private final PaymentService paymentService;

    /** Make a payment for a transaction */
    @PostMapping
    public ResponseEntity<PaymentResponse> pay(@RequestBody @Valid MakePaymentRequest req,
                                               @RequestHeader(value = "Idempotency-Key", required = false) String idemKey) {
        return ResponseEntity.status(HttpStatus.CREATED).body(paymentService.makePayment(req, idemKey));
    }

    @GetMapping("/{id}")
    public ResponseEntity<PaymentResponse> get(@PathVariable Integer id) {
        Optional<PaymentResponse> resp = paymentService.get(id);
        return resp.map(ResponseEntity::ok).orElseGet(() -> ResponseEntity.notFound().build());
    }

    /** Retry a failed payment */
    @PostMapping("/{id}/retry")
    public ResponseEntity<PaymentResponse> retry(@PathVariable Integer id,
                                                 @RequestHeader(value = "Idempotency-Key", required = false) String idemKey) {
        return ResponseEntity.ok(paymentService.retry(id, idemKey));
    }

    /** Optional: explicitly mark as failed with reason */
    @PostMapping("/{id}/fail")
    public ResponseEntity<PaymentResponse> fail(@PathVariable Integer id,
                                                @RequestParam String reasonCode,
                                                @RequestHeader(value = "Idempotency-Key", required = false) String idemKey) {
        return ResponseEntity.ok(paymentService.markFailed(id, reasonCode, idemKey));
    }
}

