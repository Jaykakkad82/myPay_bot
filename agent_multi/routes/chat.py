# agent_multi/routes/chat.py
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid

from ..workflow.graph import build_multi_agent_graph
from ..workflow.approvals import ApprovalStore
from fastapi.encoders import jsonable_encoder


graph = build_multi_agent_graph()
router = APIRouter()

class ChatIn(BaseModel):
    sessionId: Optional[str] = None
    message: str
    extras: Optional[Dict[str, Any]] = None  # {customerId, from, to, currency}

def _compose_input(message: str, extras: Optional[Dict[str, Any]]) -> str:
    if not extras:
        return message
    hints = []
    if extras.get("customerId") is not None: hints.append(f'customerId={extras["customerId"]}')
    if extras.get("from"): hints.append(f'from={extras["from"]}')
    if extras.get("to"): hints.append(f'to={extras["to"]}')
    if extras.get("currency"): hints.append(f'fxBase={extras["currency"]}')
    if hints:
        return f"{message}\n\n[context: " + ", ".join(hints) + "]"
    return message

def _format_message_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    # Prefer the summarizer’s text
    content = None
    if isinstance(state.get("result"), dict) and "summary" in state["result"]:
        content = state["result"]["summary"]
    else:
        content = "Here’s what I found:\n\n```json\n" + \
                  (state.get("result") and str(state["result"])) + "\n```"

    # pending approval banner
    pending = None
    if state.get("status") == "AWAITING_APPROVAL":
        p = state.get("pending_approval") or {}
        pending = {
            "reason": p.get("reason") or state.get("risk"),
            "args": (p.get("args") or {}),
            "approval_id": p.get("approval_id") or state.get("approval_id"),
        }

    return {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": content,
        "trace": state.get("trace") or [],
        "tool_calls": state.get("tool_calls") or [],
        "pending_approval": pending,
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "resume": jsonable_encoder(state),
    }

@router.get("/health")
async def health():
    return {"ok": True}

@router.post("/chat")
async def chat(body: ChatIn):
    initial = {
        "input": _compose_input(body.message, body.extras),
        "messages": [],
        "trace": [],
        "tool_calls": [],
    }
    state = await graph.ainvoke(initial)
    return _format_message_from_state(state)
