from mcpServer.runtime import mcp

from mcpServer.payments_api.client import PaymentsApiClient
from mcpServer.models.dto import CreateCustomerIn, GetCustomerIn, ListCustomerTxIn
from mcpServer.util.auth import assert_mcp_auth

@mcp.tool(name="create_customer", description="Create a customer if it does not exist by email; returns existing if already present.")
async def create_customer(input: CreateCustomerIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    try:
        result = await api.create_customer(input.model_dump(by_alias=True, exclude_none=True))
        return result
    finally:
        await api.close()

@mcp.tool(name="get_customer", description="Fetch a customer by id.")
async def get_customer(input: GetCustomerIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    try:
        return await api.get_customer(input.id)
    finally:
        await api.close()

@mcp.tool(name="list_customer_transactions", description="List transactions for a customer with optional filters/pagination.")
async def list_customer_transactions(input: ListCustomerTxIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    params = {
        "status": input.status or None,
        "category": input.category or None,
        "currency": input.currency or None,
        "from": input.from_,
        "to": input.to,
        "page": input.page,
        "size": input.size,
        "sort": input.sort,
    }
    try:
        return await api.list_customer_transactions(input.id, params)
    finally:
        await api.close()