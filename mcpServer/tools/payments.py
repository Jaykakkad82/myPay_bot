from mcpServer.runtime import mcp

from mcpServer.payments_api.client import PaymentsApiClient
from mcpServer.models.dto import (
    MakePaymentIn, GetPaymentIn, GetPaymentByTxIn, RetryPaymentIn, FailPaymentIn
)
from ..util.auth import assert_mcp_auth

@mcp.tool(name="make_payment", description="Make a payment for a transaction.")
async def make_payment(input: MakePaymentIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    try:
        return await api.make_payment({"transactionId": input.transactionId, "method": input.method}, input.idempotencyKey)
    finally:
        await api.close()

@mcp.tool(name="get_payment", description="Fetch a payment by id.")
async def get_payment(input: GetPaymentIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    try:
        return await api.get_payment(input.id)
    finally:
        await api.close()

@mcp.tool(name="get_payment_by_transaction", description="Fetch payment by transaction id.")
async def get_payment_by_transaction(input: GetPaymentByTxIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    try:
        return await api.get_payment_by_tx(input.transactionId)
    finally:
        await api.close()

@mcp.tool(name="retry_payment", description="Retry a failed payment.")
async def retry_payment(input: RetryPaymentIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    try:
        return await api.retry_payment(input.id, input.idempotencyKey)
    finally:
        await api.close()

@mcp.tool(name="fail_payment", description="Mark a payment as failed with a reason code.")
async def fail_payment(input: FailPaymentIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    try:
        return await api.fail_payment(input.id, input.reasonCode, input.idempotencyKey)
    finally:
        await api.close()
