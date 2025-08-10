package com.mcp.myPayments.dto.analytics;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

public record TimeSeriesResponse(
        Integer customerId,
        String bucket,                   // day | week | month
        String category,                 // optional
        List<Point> series
) {
    public record Point(
            LocalDateTime timestampStart,  // bucket start
            BigDecimal amount
    ) {}
}
