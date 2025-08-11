from mcpServer.runtime import mcp


from mcpServer.payments_api.client import PaymentsApiClient
from mcpServer.models.dto import SpendSummaryIn, SpendByCategoryIn, TimeSeriesIn
from mcpServer.util.auth import assert_mcp_auth
from mcpServer.config import DEFAULT_FX_BASE

@mcp.tool(name="spend_summary", description="Summarize completed spend for a customer in a time window.")
async def spend_summary(input: SpendSummaryIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    params = {
        "customerId": input.customerId,
        "from": input.from_,
        "to": input.to,
        "fxBase": input.fxBase or DEFAULT_FX_BASE,
    }
    try:
        return await api.spend_summary(params)
    finally:
        await api.close()

@mcp.tool(name="spend_by_category", description="Category-wise spend totals for a customer.")
async def spend_by_category(input: SpendByCategoryIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    params = {"customerId": input.customerId, "from": input.from_, "to": input.to}
    try:
        return await api.spend_by_category(params)
    finally:
        await api.close()

@mcp.tool(name="time_series", description="Time-series (day|week|month) spend for a customer; optional category filter.")
async def time_series(input: TimeSeriesIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    params = {
        "customerId": input.customerId,
        "bucket": input.bucket,
        "from": input.from_,
        "to": input.to,
        "category": input.category,
    }
    try:
        return await api.time_series(params)
    finally:
        await api.close()
