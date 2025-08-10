package com.mcp.myPayments.service;

import com.mcp.myPayments.dto.request.CreateTransactionRequest;
import com.mcp.myPayments.dto.response.TransactionResponse;
import com.mcp.myPayments.exception.NotFoundException;
import com.mcp.myPayments.mapper.TransactionMapper;
import com.mcp.myPayments.model.Customer;
import com.mcp.myPayments.model.Transaction;
import com.mcp.myPayments.repository.TransactionRepository;
import com.mcp.myPayments.service.spec.TransactionSpecs;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Optional;

import static org.springframework.data.jpa.domain.Specification.where;

@Service
@RequiredArgsConstructor
public class TransactionService {

    private final TransactionRepository txRepo;
    private final CustomerService customerService;
    private final TransactionMapper mapper;

    @Transactional
    public TransactionResponse create(CreateTransactionRequest req, String idempotencyKey) {
        // TODO: implement real idempotency using a store keyed by idempotencyKey
        Customer customer = customerService.mustGet(req.customerId());
        Transaction tx = mapper.toEntity(req, customer);
        Transaction saved = txRepo.save(tx);
        return mapper.toResponse(saved);
    }

    public Optional<TransactionResponse> get(Integer id) {
        return txRepo.findById(id).map(mapper::toResponse);
    }

    public Page<TransactionResponse> listForCustomer(Integer customerId, String status, String category, String currency,
                                                     LocalDateTime from, LocalDateTime to, Pageable pageable) {
        Specification<Transaction> spec = where(TransactionSpecs.byCustomerId(customerId))
                .and(TransactionSpecs.byStatus(status))
                .and(TransactionSpecs.byCategory(category))
                .and(TransactionSpecs.byCurrency(currency))
                .and(TransactionSpecs.createdFrom(from))
                .and(TransactionSpecs.createdTo(to));
        return txRepo.findAll(spec, pageable).map(mapper::toResponse);
    }

    public Page<TransactionResponse> search(Integer customerId, String status, String category, String currency,
                                            LocalDateTime from, LocalDateTime to, Pageable pageable) {
        Specification<Transaction> spec = where(TransactionSpecs.byCustomerId(customerId))
                .and(TransactionSpecs.byStatus(status))
                .and(TransactionSpecs.byCategory(category))
                .and(TransactionSpecs.byCurrency(currency))
                .and(TransactionSpecs.createdFrom(from))
                .and(TransactionSpecs.createdTo(to));
        return txRepo.findAll(spec, pageable).map(mapper::toResponse);
    }

    @Transactional
    public TransactionResponse cancel(Integer id, String idempotencyKey) {
        Transaction tx = txRepo.findById(id).orElseThrow(() -> new NotFoundException("Transaction not found: " + id));
        if (tx.getStatus() == Transaction.Status.COMPLETED) {
            throw new IllegalStateException("Cannot cancel a COMPLETED transaction");
        }
        tx.setStatus(Transaction.Status.FAILED);
        return mapper.toResponse(tx);
    }
}
