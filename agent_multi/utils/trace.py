# agent_multi/utils/trace.py
from typing import Any, Dict, Optional

def push_trace(state: Dict[str, Any], node: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    tr = list(state.get("trace") or [])
    tr.append({"node": node, "status": status, **({"details": details} if details else {})})
    state["trace"] = tr

def push_tool_call(state: Dict[str, Any], tool: str, args: Dict[str, Any]) -> None:
    calls = list(state.get("tool_calls") or [])
    calls.append({"tool": tool, "args": args})
    state["tool_calls"] = calls
