from mcpServer.runtime import mcp

from mcpServer.payments_api.client import PaymentsApiClient
from mcpServer.models.dto import (
    CreateTransactionIn, GetTransactionIn, SearchTransactionsIn, CancelTransactionIn
)
from ..util.auth import assert_mcp_auth

@mcp.tool(name="create_transaction", description="Create a transaction for a customer.")
async def create_transaction(input: CreateTransactionIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    payload = {
        "customerId": input.customerId,
        "amount": input.amount,
        "currency": input.currency,
        "category": input.category,
        "description": input.description,
    }
    try:
        return await api.create_transaction(payload, input.idempotencyKey)
    finally:
        await api.close()

@mcp.tool(name="get_transaction", description="Fetch a transaction by id.")
async def get_transaction(input: GetTransactionIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    try:
        return await api.get_transaction(input.id)
    finally:
        await api.close()

@mcp.tool(name="search_transactions", description="Search transactions with filters and pagination.")
async def search_transactions(input: SearchTransactionsIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    params = {
        "customerId": input.customerId,
        "status": input.status,
        "category": input.category,
        "currency": input.currency,
        "from": input.from_,
        "to": input.to,
        "page": input.page,
        "size": input.size,
        "sort": input.sort,
    }
    try:
        return await api.search_transactions({k: v for k, v in params.items() if v not in (None, "")})
    finally:
        await api.close()

@mcp.tool(name="cancel_transaction", description="Cancel a pending transaction (sets FAILED).")
async def cancel_transaction(input: CancelTransactionIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    try:
        return await api.cancel_transaction(input.id, input.idempotencyKey)
    finally:
        await api.close()
