from mcpServer.runtime import mcp
from mcpServer.payments_api.client import PaymentsApiClient

@mcp.resource(
    uri="resource://customers/{id}",
    name="customers",
    description="Customer profile JSON",
    mime_type="application/json",
)
async def customer_resource(id: str) -> dict:                  
    api = PaymentsApiClient()
    try:
        return await api.get_customer(int(id))
    finally:
        await api.close()
