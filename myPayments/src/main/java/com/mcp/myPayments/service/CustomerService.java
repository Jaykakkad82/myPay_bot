package com.mcp.myPayments.service;

import com.mcp.myPayments.dto.request.CreateCustomerRequest;
import com.mcp.myPayments.dto.response.CustomerResponse;
import com.mcp.myPayments.exception.NotFoundException;
import com.mcp.myPayments.mapper.CustomerMapper;
import com.mcp.myPayments.model.Customer;
import com.mcp.myPayments.repository.CustomerRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
@RequiredArgsConstructor
public class CustomerService {

    private final CustomerRepository repo;
    private final CustomerMapper mapper;

    @Transactional
    public CustomerResponse create(CreateCustomerRequest req) {
//        Customer entity = mapper.toEntity(req);
//        Customer saved = repo.save(entity);
//        return mapper.toResponse(saved);
        // 1) Upsert-ish: if email exists, return existing with 200
        var existing = repo.findByEmail(req.email());
        if (existing.isPresent()) {
            var resp = mapper.toResponse(existing.get());
            return resp; // controller returns 200 OK
        }

        // 2) Otherwise create
        var entity = mapper.toEntity(req);
        var saved  = repo.save(entity);
        return mapper.toResponse(saved); // controller returns 201 Created
    }

    public Optional<CustomerResponse> get(Integer id) {
        return repo.findById(id).map(mapper::toResponse);
    }

    public Customer mustGet(Integer id) {
        return repo.findById(id).orElseThrow(() -> new NotFoundException("Customer not found: " + id));
    }
}

