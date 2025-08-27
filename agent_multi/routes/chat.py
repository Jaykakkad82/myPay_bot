# agent_multi/routes/chat.py
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid

from fastapi.encoders import jsonable_encoder

from ..workflow.graph import build_multi_agent_graph
from ..workflow.sessions import SessionMemory  # per-session memory

graph = build_multi_agent_graph()
router = APIRouter()


class ChatIn(BaseModel):
    sessionId: Optional[str] = None
    message: str
    extras: Optional[Dict[str, Any]] = None  # {customerId, from, to, currency}


def _compose_input(message: str, extras: Optional[Dict[str, Any]]) -> str:
    """
    Attach structured hints for the planner/agents (keeps your existing UI extras).
    """
    if not extras:
        return message
    hints = []
    if extras.get("customerId") is not None:
        hints.append(f'customerId={extras["customerId"]}')
    if extras.get("from"):
        hints.append(f'from={extras["from"]}')
    if extras.get("to"):
        hints.append(f'to={extras["to"]}')
    if extras.get("currency"):
        hints.append(f'fxBase={extras["currency"]}')
    if hints:
        return f"{message}\n\n[context: " + ", ".join(hints) + "]"
    return message


def _format_message_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Shape the assistant turn for the UI (summary first, fallback to raw JSON),
    and include a resume blob so approvals can continue the graph.
    """
    # Prefer the summarizer’s text
    if isinstance(state.get("result"), dict) and "summary" in state["result"]:
        content = state["result"]["summary"]
    else:
        content = "Here’s what I found:\n\n```json\n" + str(state.get("result")) + "\n```"

    # Pending approval banner (if any)
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
        # Client uses this to resume on Approve/Reject
        "resume": jsonable_encoder(state),
        # Optional: if you ever emit notifications in the graph
        "notifications": state.get("notifications") or [],
    }


@router.get("/health")
async def health():
    return {"ok": True}


@router.post("/chat")
async def chat(body: ChatIn):
    """
    - Keep per-session chat history (user/assistant turns) with SessionMemory
    - Pass history + scratch into the graph
    - Persist last_result back to scratch for follow-ups
    - Return a UI-friendly assistant message + resume blob
    """
    # 1) Resolve session and compose the model input
    sid = body.sessionId or "default"
    user_text = (body.message or "").strip()
    composed = _compose_input(user_text, body.extras)

    # 2) Load session memory (history + scratch) and append the user turn
    mem = SessionMemory.get(sid)
    history = mem["messages"]                    # list of {role, content}
    SessionMemory.append(sid, "user", user_text) # store raw user text (not composed)

    # 3) Build the initial graph state
    initial = {
        "input": composed,                       # includes [context: ...] if extras
        "messages": history,                     # orchestrator/agents can read conversation so far
        "scratch": SessionMemory.get_scratch(sid),
        "trace": [],
        "tool_calls": [],
    }

    # 4) Run the graph
    state = await graph.ainvoke(initial)

    # 5) Persist useful scratch for next turns (e.g., last_result, last ids)
    scratch = state.get("scratch") or {}
    if "last_result" in scratch:
        SessionMemory.put_scratch(sid, "last_result", scratch["last_result"])

    # 6) Format assistant turn and append to memory
    msg = _format_message_from_state(state)
    SessionMemory.append(sid, "assistant", msg["content"])

    # 7) Return to UI
    return msg
