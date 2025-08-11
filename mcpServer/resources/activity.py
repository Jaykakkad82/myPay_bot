from mcpServer.runtime import mcp

from mcpServer.payments_api.client import PaymentsApiClient

@mcp.resource(name="recent-activity", 
description="Recent transactions for a customer", 
uri="resource://customers/{id}/recent",
mime_type="application/json"
)
async def recent_activity_resource(id: str) -> dict:
    api = PaymentsApiClient()
    try:
        # last 7 days, page 0, size 10
        from datetime import datetime, timedelta
        to = datetime.utcnow().replace(microsecond=0).isoformat()
        from_ = (datetime.utcnow() - timedelta(days=7)).replace(microsecond=0).isoformat()
        params = {"from": from_, "to": to, "page": 0, "size": 10, "sort": "createdAt,desc"}
        return await api.list_customer_transactions(int(id), params)
    finally:
        await api.close()
