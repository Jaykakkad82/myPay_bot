from ..config import MCP_SERVER_API_KEY

def assert_mcp_auth(headers: dict):
    if MCP_SERVER_API_KEY:
        incoming = headers.get("X-MCP-Api-Key") or headers.get("x-mcp-api-key")
        if incoming != MCP_SERVER_API_KEY:
            raise PermissionError("Unauthorized MCP request")
