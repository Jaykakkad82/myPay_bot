package com.mcp.myPayments.service;

import com.mcp.myPayments.dto.request.MakePaymentRequest;
import com.mcp.myPayments.dto.response.PaymentResponse;
import com.mcp.myPayments.exception.NotFoundException;
import com.mcp.myPayments.mapper.PaymentMapper;
import com.mcp.myPayments.model.Payment;
import com.mcp.myPayments.model.Transaction;
import com.mcp.myPayments.repository.PaymentRepository;
import com.mcp.myPayments.repository.TransactionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
@RequiredArgsConstructor
public class PaymentService {

    private final PaymentRepository payRepo;
    private final TransactionRepository txRepo;
    private final PaymentMapper mapper;

    public Optional<PaymentResponse> get(Integer id) {
        return payRepo.findById(id).map(p -> mapper.toResponse(p, null));
    }

    public Optional<PaymentResponse> getByTransactionId(Integer txId) {
        return payRepo.findByTransaction_Id(txId).map(p -> mapper.toResponse(p, null));
    }

    @Transactional
    public PaymentResponse makePayment(MakePaymentRequest req, String idempotencyKey) {
        // TODO: real idempotency using idempotencyKey + transactionId
        Transaction tx = txRepo.findById(req.transactionId())
                .orElseThrow(() -> new NotFoundException("Transaction not found: " + req.transactionId()));

        // If payment already exists, return it (idempotent-ish)
        Optional<Payment> existing = payRepo.findByTransaction_Id(tx.getId());
        if (existing.isPresent()) {
            return mapper.toResponse(existing.get(), null);
        }

        Payment payment = mapper.toNewPayment(req, tx);

        // Simulate gateway result (stub). Replace with real gateway integration.
        payment.setStatus(Payment.Status.SUCCESS);
        tx.setStatus(Transaction.Status.COMPLETED);

        Payment saved = payRepo.save(payment);
        return mapper.toResponse(saved, null);
    }

    @Transactional
    public PaymentResponse retry(Integer paymentId, String idempotencyKey) {
        Payment p = payRepo.findById(paymentId)
                .orElseThrow(() -> new NotFoundException("Payment not found: " + paymentId));

        if (p.getStatus() == Payment.Status.SUCCESS) {
            return mapper.toResponse(p, null);
        }

        // Simulate retry
        p.setStatus(Payment.Status.SUCCESS);
        Transaction tx = p.getTransaction();
        tx.setStatus(Transaction.Status.COMPLETED);

        return mapper.toResponse(p, null);
    }

    @Transactional
    public PaymentResponse markFailed(Integer paymentId, String reasonCode, String idempotencyKey) {
        Payment p = payRepo.findById(paymentId)
                .orElseThrow(() -> new NotFoundException("Payment not found: " + paymentId));

        p.setStatus(Payment.Status.FAILED);
        Transaction tx = p.getTransaction();
        tx.setStatus(Transaction.Status.FAILED);

        // NOTE: reasonCode not persisted yet; consider a PaymentEvent table to store it.
        return mapper.toResponse(p, reasonCode);
    }
}

