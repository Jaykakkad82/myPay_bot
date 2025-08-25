from typing import Any, Dict, Optional
from fastmcp import Client

class MCPBridge:
    """Minimal wrapper; collects tool_call traces for the UI."""
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.headers = headers or {}
        self._client: Optional[Client] = None
        self.calls = []  # list of {"tool", "args"}

    async def __aenter__(self):
        self._client = Client(self.url)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.__aexit__(exc_type, exc, tb)
            self._client = None

    async def call(self, name: str, args: Dict[str, Any]):
        assert self._client is not None
        payload = {"input": args, "headers": self.headers} if self.headers else {"input": args}
        self.calls.append({"tool": name, "args": args})
        res = await self._client.call_tool(name, payload)
        # Favor structured_content/data if present
        return getattr(res, "structured_content", None) or getattr(res, "data", None) or {}

def auth_headers(api_key: Optional[str]) -> Optional[Dict[str, str]]:
    return {"x-mcp-api-key": api_key} if api_key else None
