package com.mcp.myPayments.repository;

import com.mcp.myPayments.model.Transaction;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TransactionRepository extends JpaRepository<Transaction, Integer> {
    Page<Transaction> findByCustomer_Id(Integer customerId, Pageable pageable);
    Page<Transaction> findAll(Specification<Transaction> spec, Pageable pageable);
}
