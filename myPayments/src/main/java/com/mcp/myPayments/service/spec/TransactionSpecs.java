package com.mcp.myPayments.service.spec;

import com.mcp.myPayments.model.Transaction;
import org.springframework.data.jpa.domain.Specification;

import java.time.LocalDateTime;

public class TransactionSpecs {

    public static Specification<Transaction> byCustomerId(Integer customerId) {
        return (root, q, cb) -> customerId == null ? null : cb.equal(root.get("customer").get("id"), customerId);
    }

    public static Specification<Transaction> byStatus(String status) {
        return (root, q, cb) -> {
            if (status == null || status.isBlank()) return null;
            try {
                return cb.equal(root.get("status"),
                        Transaction.Status.valueOf(status.toUpperCase()));
            } catch (IllegalArgumentException ex) {
                // unknown status -> no matches (or throw 400 if you prefer)
                return cb.disjunction();
            }
        };
    }

    public static Specification<Transaction> byCategory(String category) {
        return (root, q, cb) -> (category == null || category.isBlank())
                ? null : cb.equal(root.get("category"), category);
    }

    public static Specification<Transaction> byCurrency(String currency) {
        return (root, q, cb) -> (currency == null || currency.isBlank())
                ? null : cb.equal(root.get("currency"), currency);
    }

    public static Specification<Transaction> createdFrom(LocalDateTime from) {
        return (root, q, cb) -> from == null ? null : cb.greaterThanOrEqualTo(root.get("createdAt"), from);
    }

    public static Specification<Transaction> createdTo(LocalDateTime to) {
        return (root, q, cb) -> to == null ? null : cb.lessThanOrEqualTo(root.get("createdAt"), to);
    }
}
