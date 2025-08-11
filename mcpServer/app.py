
import os
from mcpServer.runtime import mcp

# Simple runner: stdio (for local dev) or http (SSE) depending on env
import os

def main():

    transport = os.getenv("MCP_TRANSPORT", "http")  # stdio | http
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8765"))

    # FastMCP auto-discovers decorated tools/resources upon import.
    from mcpServer.tools import customers, transactions, payments, analytics   
    from mcpServer.resources import customers as r_customers, activity as r_activity


    if transport == "http":
        print(f"[myPayments-mcp] HTTP/SSE on {host}:{port}")
        mcp.run(transport="http", host=host, port=port)   # <-- no await / no asyncio.run
    else:
        print("[myPayments-mcp] stdio mode")
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
