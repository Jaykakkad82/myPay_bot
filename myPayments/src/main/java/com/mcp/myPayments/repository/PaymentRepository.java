package com.mcp.myPayments.repository;

import com.mcp.myPayments.model.Payment;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface PaymentRepository extends JpaRepository<Payment, Integer> {
    Optional<Payment> findByTransaction_Id(Integer transactionId);
}

