package com.mcp.myPayments.mapper;

import com.mcp.myPayments.dto.request.CreateTransactionRequest;
import com.mcp.myPayments.dto.response.TransactionResponse;
import com.mcp.myPayments.model.Customer;
import com.mcp.myPayments.model.Transaction;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
public class TransactionMapper {

    /** Builds a Transaction entity; caller must set the Customer association. */
    public Transaction toEntity(CreateTransactionRequest req, Customer customer) {
        if (req == null) return null;
        var tx = new Transaction();
        tx.setCustomer(customer);
        tx.setAmount(req.amount());
        tx.setCurrency(req.currency());
        tx.setCategory(req.category());
        tx.setStatus(Transaction.Status.PENDING);
        tx.setCreatedAt(LocalDateTime.now());
        tx.setDescription(req.description());
        return tx;
    }

    public TransactionResponse toResponse(Transaction t) {
        if (t == null) return null;
        return new TransactionResponse(
                t.getId(),
                t.getCustomer() != null ? t.getCustomer().getId() : null,
                t.getAmount(),
                t.getCurrency(),
                t.getCategory(),
                t.getStatus() != null ? t.getStatus().name() : null,
                t.getCreatedAt(),
                t.getDescription()
        );
    }
}
