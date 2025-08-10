package com.mcp.myPayments.analytics;

import com.mcp.myPayments.dto.analytics.CategorySpendResponse;
import com.mcp.myPayments.dto.analytics.SpendSummaryResponse;
import com.mcp.myPayments.dto.analytics.TimeSeriesResponse;
import com.mcp.myPayments.mapper.AnalyticsMapper;
import com.mcp.myPayments.model.Transaction;
import com.mcp.myPayments.repository.TransactionRepository;
import com.mcp.myPayments.service.spec.TransactionSpecs;
import lombok.RequiredArgsConstructor;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.temporal.WeekFields;
import java.util.*;
import java.util.stream.Collectors;

import static org.springframework.data.jpa.domain.Specification.where;

@Service
@RequiredArgsConstructor
public class AnalyticsService {

    private final TransactionRepository txRepo;
    private final AnalyticsMapper mapper;

    public SpendSummaryResponse spendSummary(Integer customerId, LocalDateTime from, LocalDateTime to, String fxBase) {
        // Simple approach: fetch filtered txns and aggregate in-memory.
        var page = txRepo.findAll(
                where(TransactionSpecs.byCustomerId(customerId))
                        .and(TransactionSpecs.createdFrom(from))
                        .and(TransactionSpecs.createdTo(to))
                        .and(TransactionSpecs.byStatus("COMPLETED")),
                org.springframework.data.domain.Pageable.unpaged()
        );

        var completed = page.getContent();
        BigDecimal total = completed.stream()
                .map(Transaction::getAmount)
                .filter(Objects::nonNull)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        long count = completed.size();
        BigDecimal avg = count == 0 ? BigDecimal.ZERO : total.divide(BigDecimal.valueOf(count), 2, java.math.RoundingMode.HALF_UP);

        // TODO: normalize multi-currency using fxBase via an FX service; currently assumes amounts are comparable as-is.
        return mapper.toSpendSummary(customerId, fxBase, total, count, avg, from, to);
    }

    public List<CategorySpendResponse> spendByCategory(Integer customerId, LocalDateTime from, LocalDateTime to) {
        var page = txRepo.findAll(
                where(TransactionSpecs.byCustomerId(customerId))
                        .and(TransactionSpecs.createdFrom(from))
                        .and(TransactionSpecs.createdTo(to))
                        .and(TransactionSpecs.byStatus("COMPLETED")),
                org.springframework.data.domain.Pageable.unpaged()
        );

        Map<String, List<Transaction>> byCat = page.getContent().stream()
                .collect(Collectors.groupingBy(Transaction::getCategory, Collectors.toList()));

        List<CategorySpendResponse> out = new ArrayList<>();
        for (var e : byCat.entrySet()) {
            BigDecimal total = e.getValue().stream()
                    .map(Transaction::getAmount).filter(Objects::nonNull)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            out.add(mapper.toCategorySpend(customerId, e.getKey(), total, (long) e.getValue().size()));
        }
        return out;
    }

    public TimeSeriesResponse timeSeries(Integer customerId, String bucket, LocalDateTime from, LocalDateTime to, String category) {
        var spec = where(TransactionSpecs.byCustomerId(customerId))
                .and(TransactionSpecs.createdFrom(from))
                .and(TransactionSpecs.createdTo(to))
                .and(TransactionSpecs.byStatus("COMPLETED"))
                .and(category == null ? null : TransactionSpecs.byCategory(category));

        var page = txRepo.findAll(spec, org.springframework.data.domain.Pageable.unpaged());
        var data = page.getContent();

        Map<LocalDateTime, BigDecimal> buckets = new TreeMap<>();

        for (var tx : data) {
            LocalDateTime ts = tx.getCreatedAt();
            LocalDateTime key = switch (bucket.toLowerCase()) {
                case "day" -> ts.withHour(0).withMinute(0).withSecond(0).withNano(0);
                case "week" -> {
                    var wf = WeekFields.ISO;
                    var firstDay = ts.with(wf.dayOfWeek(), 1).withHour(0).withMinute(0).withSecond(0).withNano(0);
                    yield firstDay;
                }
                case "month" -> ts.withDayOfMonth(1).withHour(0).withMinute(0).withSecond(0).withNano(0);
                default -> throw new IllegalArgumentException("bucket must be day|week|month");
            };
            buckets.merge(key, tx.getAmount(), (a, b) -> a.add(b));
        }

        var series = buckets.entrySet().stream()
                .map(e -> mapper.toPoint(e.getKey(), e.getValue()))
                .toList();

        return mapper.toTimeSeries(customerId, bucket, category, series);
    }
}

