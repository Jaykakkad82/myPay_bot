from mcpServer.runtime import mcp


from mcpServer.payments_api.client import PaymentsApiClient
from mcpServer.models.dto import SpendSummaryIn, SpendByCategoryIn, TimeSeriesIn, SpendByCategoryOut
from mcpServer.util.auth import assert_mcp_auth
from mcpServer.config import DEFAULT_FX_BASE
from datetime import datetime

ISO_FMT = "%Y-%m-%dT%H:%M:%S"

def _normalize_iso(dt: str, is_end: bool = False) -> str:
    if dt is None:
        return None
    dt = dt.strip()
    # If only a date is provided, expand to start/end of day
    if len(dt) == 10 and dt.count("-") == 2:  # 'YYYY-MM-DD'
        return f"{dt}T23:59:59" if is_end else f"{dt}T00:00:00"
    # Accept already-ISO (with or without seconds)
    if "T" in dt:
        # trim microseconds / timezone if present
        try:
            # try parse with seconds
            datetime.strptime(dt[:19], ISO_FMT)
            return dt[:19]
        except ValueError:
            # try "YYYY-MM-DDTHH:MM"
            try:
                base = dt[:16]  # minutes
                datetime.strptime(base, "%Y-%m-%dT%H:%M")
                return f"{base}:00"
            except ValueError:
                pass
    # As a last resort, raise a helpful error
    raise ValueError(f"Invalid datetime format: {dt}. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM[:SS]")



@mcp.tool(name="spend_summary", description="Summarize completed spend for a customer in a time window.")
async def spend_summary(input: SpendSummaryIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    params = {
        "customerId": input.customerId,
        "from": _normalize_iso(input.from_),
        "to": _normalize_iso(input.to),
        "fxBase": input.fxBase or DEFAULT_FX_BASE,
    }
    try:
        return await api.spend_summary(params)
    finally:
        await api.close()

@mcp.tool(name="spend_by_category", 
          description="Category-wise spend totals for a customer.", 
          output_schema=SpendByCategoryOut.model_json_schema())
async def spend_by_category(input: SpendByCategoryIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    print("Request received with parameters: ", input)
    api = PaymentsApiClient()
    params = {"customerId": input.customerId, "from": _normalize_iso(input.from_), "to": _normalize_iso(input.to)}
    try:
        raw = await api.spend_by_category(params)  # upstream may return a list
        print(raw)
        # Normalize to a dict for FastMCP
        if isinstance(raw, dict):
            items = raw.get("items", [])
        else:
            items = raw or []

        normalized = {
            "customerId": input.customerId,
            "from_": params["from"],
            "to": params["to"],
            "baseCurrency": DEFAULT_FX_BASE,
            "items": [
            {
                "category": r.get("category", ""),
                "amount": float(r.get("totalAmount", 0) or 0),
                "transactionCount": r.get("transactionCount", 0),
                "currency": r.get("currency", DEFAULT_FX_BASE),
            }
            for r in items
            ],
        }
        print("Normalized spend by category:", normalized)
        return normalized
    finally:
        await api.close()

@mcp.tool(name="time_series", description="Time-series (day|week|month) spend for a customer; optional category filter.")
async def time_series(input: TimeSeriesIn, headers: dict) -> dict:
    assert_mcp_auth(headers)
    api = PaymentsApiClient()
    params = {
        "customerId": input.customerId,
        "bucket": input.bucket,
        "from": _normalize_iso(input.from_),
        "to": _normalize_iso(input.to),
        "category": input.category,
    }
    try:
        return await api.time_series(params)
    finally:
        await api.close()
