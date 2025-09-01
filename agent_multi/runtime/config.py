# agent_multi/runtime/config.py
import os, math

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DDB_TABLE  = os.getenv("DDB_TABLE", "mp-runtime")
DDB_TTL_DAYS = int(os.getenv("DDB_TTL_DAYS", "2"))
DDB_ENDPOINT = os.getenv("DDB_ENDPOINT","http://localhost:8000")

# Tier limit templates (tune as you like)
ANON_LIMITS = {
    "requests_per_min": int(os.getenv("LIMIT_ANON_REQ_PER_MIN", "12")),
    "tools_per_min":    int(os.getenv("LIMIT_ANON_TOOL_PER_MIN", "12")),
    "tokens_per_day":   int(os.getenv("LIMIT_ANON_TOK_PER_DAY", "60000")),
}
ELEV_LIMITS = {
    "requests_per_min": int(os.getenv("LIMIT_ELEV_REQ_PER_MIN", "60")),
    "tools_per_min":    int(os.getenv("LIMIT_ELEV_TOOL_PER_MIN", "60")),
    "tokens_per_day":   int(os.getenv("LIMIT_ELEV_TOK_PER_DAY", "300000")),
}
ADMIN_LIMITS = {
    "requests_per_min": math.inf,
    "tools_per_min":    math.inf,
    "tokens_per_day":   math.inf,
}

# Access keys (optional upgrade)
ACCESS_KEY_ELEVATED = os.getenv("ACCESS_KEY_ELEVATED", "")
ACCESS_KEY_ADMIN    = os.getenv("ACCESS_KEY_ADMIN", "")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
