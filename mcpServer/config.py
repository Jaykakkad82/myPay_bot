import os

MY_PAYMENTS_BASE_URL = os.getenv("MY_PAYMENTS_BASE_URL", "http://localhost:12136/api/v1/service")
MY_PAYMENTS_API_KEY  = os.getenv("MY_PAYMENTS_API_KEY", "lovethisapp")          # forwarded to Spring
MCP_SERVER_API_KEY   = os.getenv("MCP_SERVER_API_KEY", "lovethisapp")           # required by clients

# HTTP
REQUEST_TIMEOUT_SECS = float(os.getenv("REQUEST_TIMEOUT_SECS", "20"))

# Defaults for analytics
DEFAULT_FX_BASE = os.getenv("DEFAULT_FX_BASE", "USD")