package com.mcp.myPayments.mapper;

import com.mcp.myPayments.dto.request.MakePaymentRequest;
import com.mcp.myPayments.dto.response.PaymentResponse;
import com.mcp.myPayments.model.Payment;
import com.mcp.myPayments.model.Transaction;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.UUID;

@Component
public class PaymentMapper {

    /**
     * Creates a Payment skeleton for a given transaction + method.
     * Caller should finalize status and persistence.
     */
    public Payment toNewPayment(MakePaymentRequest req, Transaction tx) {
        if (req == null || tx == null) return null;
        var p = new Payment();
        p.setTransaction(tx);
        p.setMethod(req.method());
        p.setStatus(Payment.Status.INITIATED);
        p.setReferenceId(UUID.randomUUID().toString());
        p.setProcessedAt(LocalDateTime.now());
        return p;
    }

    public PaymentResponse toResponse(Payment p, String failureReason) {
        if (p == null) return null;
        return new PaymentResponse(
                p.getId(),
                p.getTransaction() != null ? p.getTransaction().getId() : null,
                p.getMethod(),
                p.getStatus() != null ? p.getStatus().name() : null,
                p.getReferenceId(),
                p.getProcessedAt(),
                failureReason
        );
    }

    /** Overload if you don’t track failure reasons yet. */
    public PaymentResponse toResponse(Payment p) {
        return toResponse(p, null);
    }
}

