
package com.mcp.myPayments.model;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Payment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @OneToOne
    @JoinColumn(name = "transaction_id", unique = true, nullable = false)
    private Transaction transaction;

    private String method;

    @Enumerated(EnumType.STRING)
    private Status status;

    private String referenceId;

    private LocalDateTime processedAt;

    public enum Status {
        INITIATED, SUCCESS, FAILED
    }
}
