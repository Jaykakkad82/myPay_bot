import os

MCP_URL     = os.getenv("MCP_URL", "http://localhost:8765/mcp/")
MCP_API_KEY = os.getenv("MCP_API_KEY", "lovethisapp")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # or any supported
APPROVAL_TIMEOUT_SECS = int(os.getenv("APPROVAL_TIMEOUT_SECS", "300"))

# Demo policy: payments >= threshold need approval
APPROVAL_AMOUNT_THRESHOLD = float(os.getenv("APPROVAL_AMOUNT_THRESHOLD", "500.0"))
