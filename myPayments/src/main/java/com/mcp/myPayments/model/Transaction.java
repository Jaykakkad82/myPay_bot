package com.mcp.myPayments.model;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Transaction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @ManyToOne
    @JoinColumn(name = "customer_id", nullable = false)
    private Customer customer;

    private BigDecimal amount;

    private String currency;

    private String category;

    @Enumerated(EnumType.STRING)
    private Status status;

    private LocalDateTime createdAt;

    private String description;

    @OneToOne(mappedBy = "transaction", cascade = CascadeType.ALL)
    private Payment payment;

    public enum Status {
        PENDING, COMPLETED, FAILED
    }
}
