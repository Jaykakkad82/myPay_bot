from typing import Any, Dict, Optional
from fastmcp import Client

class MCPBridge:
    """Thin async wrapper around fastmcp.Client with simple helpers."""

    def __init__(self, url: str):
        self.url = url
        self._client: Optional[Client] = None

    async def __aenter__(self):
        self._client = Client(self.url)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.__aexit__(exc_type, exc, tb)
            self._client = None

    async def call(self, name: str, input_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None):
        """Call an MCP tool. Server schema expects {'input': ..., 'headers': ...?}."""
        if not self._client:
            raise RuntimeError("MCPBridge not started. Use 'async with MCPBridge(...)'.")
        payload: Dict[str, Any] = {"input": input_payload}
        if headers:
            payload["headers"] = headers
        result = await self._client.call_tool(name, payload)
        # Prefer structured JSON; fallback to text
        return result.structured_content or result.data or (result.content[0].text if result.content else None)

    async def read(self, uri: str):
        if not self._client:
            raise RuntimeError("MCPBridge not started.")
        res = await self._client.read_resource(uri)
        # read_resource returns a list of contents; unwrap the first if text
        if res and hasattr(res[0], "text"):
            return res[0].text
        return res

    async def list_tools(self):
        if not self._client:
            raise RuntimeError("MCPBridge not started.")
        return await self._client.list_tools()

    async def list_resource_templates(self):
        if not self._client:
            raise RuntimeError("MCPBridge not started.")
        return await self._client.list_resource_templates()
