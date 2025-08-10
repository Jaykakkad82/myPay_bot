package com.mcp.myPayments.controllers;

import com.mcp.myPayments.dto.analytics.CategorySpendResponse;
import com.mcp.myPayments.dto.analytics.SpendSummaryResponse;
import com.mcp.myPayments.dto.analytics.TimeSeriesResponse;
import com.mcp.myPayments.analytics.AnalyticsService;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.format.annotation.DateTimeFormat.ISO;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/v1/service/analytics")
@RequiredArgsConstructor
public class AnalyticsController {

    private final AnalyticsService analyticsService;

    @GetMapping("/spend-summary")
    public ResponseEntity<SpendSummaryResponse> spendSummary(
            @RequestParam Integer customerId,
            @RequestParam @DateTimeFormat(iso = ISO.DATE_TIME) LocalDateTime from,
            @RequestParam @DateTimeFormat(iso = ISO.DATE_TIME) LocalDateTime to,
            @RequestParam(defaultValue = "USD") String fxBase
    ) {
        return ResponseEntity.ok(analyticsService.spendSummary(customerId, from, to, fxBase));
    }

    @GetMapping("/spend-by-category")
    public ResponseEntity<List<CategorySpendResponse>> spendByCategory(
            @RequestParam Integer customerId,
            @RequestParam @DateTimeFormat(iso = ISO.DATE_TIME) LocalDateTime from,
            @RequestParam @DateTimeFormat(iso = ISO.DATE_TIME) LocalDateTime to
    ) {
        return ResponseEntity.ok(analyticsService.spendByCategory(customerId, from, to));
    }

    @GetMapping("/time-series")
    public ResponseEntity<TimeSeriesResponse> timeSeries(
            @RequestParam Integer customerId,
            @RequestParam String bucket, // day|week|month
            @RequestParam @DateTimeFormat(iso = ISO.DATE_TIME) LocalDateTime from,
            @RequestParam @DateTimeFormat(iso = ISO.DATE_TIME) LocalDateTime to,
            @RequestParam(required = false) String category
    ) {
        return ResponseEntity.ok(analyticsService.timeSeries(customerId, bucket, from, to, category));
    }
}

