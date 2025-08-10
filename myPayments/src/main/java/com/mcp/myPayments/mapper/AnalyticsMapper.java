package com.mcp.myPayments.mapper;

import com.mcp.myPayments.dto.analytics.CategorySpendResponse;
import com.mcp.myPayments.dto.analytics.SpendSummaryResponse;
import com.mcp.myPayments.dto.analytics.TimeSeriesResponse;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Component
public class AnalyticsMapper {

    public SpendSummaryResponse toSpendSummary(
            Integer customerId,
            String baseCurrency,
            BigDecimal totalAmount,
            Long transactionCount,
            BigDecimal averageTicket,
            LocalDateTime from,
            LocalDateTime to
    ) {
        return new SpendSummaryResponse(
                customerId,
                baseCurrency,
                totalAmount != null ? totalAmount : BigDecimal.ZERO,
                transactionCount != null ? transactionCount : 0,
                averageTicket != null ? averageTicket : BigDecimal.ZERO,
                from != null ? from.toString() : null,
                to != null ? to.toString() : null
        );
    }

    public CategorySpendResponse toCategorySpend(
            Integer customerId,
            String category,
            BigDecimal totalAmount,
            Long transactionCount
    ) {
        return new CategorySpendResponse(
                customerId,
                category,
                totalAmount != null ? totalAmount : BigDecimal.ZERO,
                transactionCount != null ? transactionCount : 0
        );
    }

    public TimeSeriesResponse toTimeSeries(
            Integer customerId,
            String bucket,
            String category,
            List<TimeSeriesResponse.Point> series
    ) {
        return new TimeSeriesResponse(
                customerId,
                bucket,
                category,
                series
        );
    }

    public TimeSeriesResponse.Point toPoint(LocalDateTime start, BigDecimal amount) {
        return new TimeSeriesResponse.Point(
                start,
                amount != null ? amount : BigDecimal.ZERO
        );
    }
}
