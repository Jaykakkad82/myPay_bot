import os

# MCP
MCP_URL = os.getenv("MCP_URL", "http://localhost:8765/mcp/")
MCP_API_KEY = os.getenv("MCP_API_KEY", "lovethisapp")  

# LLM
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # required for LangChain OpenAI

# Behavior
MAX_WINDOW_DAYS = int(os.getenv("MAX_WINDOW_DAYS", "90"))
VERBOSE = bool(int(os.getenv("VERBOSE", "1")))
