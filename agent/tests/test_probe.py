import asyncio
import os
from agent.mcp_bridge import MCPBridge
from agent.config import MCP_URL

async def _probe():
    async with MCPBridge(MCP_URL) as mcp:
        tools = await mcp.list_tools()
        assert tools and len(tools) > 0

def test_mcp_probe():
    asyncio.run(_probe())