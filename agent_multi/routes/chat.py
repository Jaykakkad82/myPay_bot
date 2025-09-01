# agent_multi/routes/chat.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import uuid
from fastapi.encoders import jsonable_encoder

from ..workflow.graph import build_multi_agent_graph
from ..workflow.sessions import SessionMemory
from ..runtime.session_store import SessionStore

graph = build_multi_agent_graph()
router = APIRouter()


class ChatIn(BaseModel):
    sessionId: Optional[str] = None
    message: str
    extras: Optional[Dict[str, Any]] = None


def _compose_input(message: str, extras: Optional[Dict[str, Any]]) -> str:
    """Render a contextual banner that the graph/agents can parse, but store raw user text in memory."""
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
    return message if not hints else f"{message}\n\n[context: " + ", ".join(hints) + "]"


def _approx_tokens(*texts: str) -> int:
    """Very rough heuristic: 1 token ≈ 4 chars."""
    total = 0
    for t in texts:
        if isinstance(t, str):
            total += len(t)
        else:
            total += len(str(t))
    return max(1, total // 4)


def _compact_history_by_chars(messages: List[Dict[str, Any]], max_chars: int = 8000) -> List[Dict[str, Any]]:
    """
    Keep the most recent turns up to ~max_chars of total content.
    Messages are expected as {role, content, ts?}.
    """
    if not messages:
        return []
    acc: List[Dict[str, Any]] = []
    used = 0
    # walk from the end (most recent) backwards
    for msg in reversed(messages):
        c = msg.get("content") or ""
        length = len(c) if isinstance(c, str) else len(str(c))
        if used + length > max_chars and acc:
            break
        acc.append(msg)
        used += length
    acc.reverse()
    return acc


def _format_message_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    # Prefer summarizer text if provided
    if isinstance(state.get("result"), dict) and "summary" in state["result"]:
        content = state["result"]["summary"]
    else:
        result_str = jsonable_encoder(state.get("result"))
        content = f"Here’s what I found:\n\n```json\n{result_str}\n```"

    # Pending approval structure for the UI banner
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
        "notifications": state.get("notifications") or [],
    }


@router.get("/health")
async def health():
    return {"ok": True}


@router.post("/chat")
async def chat(body: ChatIn, request: Request):
    # --- Require server session (aligns with your new SessionStore) ---
    sid = body.sessionId or request.headers.get("X-Session-Id")
    if not sid:
        raise HTTPException(status_code=401, detail="missing sessionId")
    if not SessionStore.get_session(sid):
        raise HTTPException(status_code=401, detail="unknown session; call /session/start")

    # --- Per-request limit check ---
    ok, meta = SessionStore.enforce_request(sid)
    if not ok:
        raise HTTPException(status_code=429, detail=meta)

    # --- Load session memory and append the user turn (store RAW user message) ---
    mem = SessionMemory.get(sid)  # expected shape: { "messages": [...], ... }
    SessionMemory.append(sid, role="user", content=body.message)

    # --- Build the text sent to the graph (user text + optional [context: ...]) ---
    user_text_for_graph = _compose_input(body.message, body.extras)

    # --- Compact history before invoking the graph (char-based; swap for tokenizer later) ---
    history = _compact_history_by_chars(mem.get("messages", []), max_chars=8000)

    # --- Invoke graph with history and extras (so notifier/compliance can use them) ---
    initial = {
        "input": user_text_for_graph,
        "messages": history,       # plain list of {role, content, ts?}
        "trace": [],
        "tool_calls": [],
        "extras": body.extras or {},
    }
    state = await graph.ainvoke(initial)

    # --- Enforce tool-call and token limits after execution (so we have counts) ---
    tool_calls = state.get("tool_calls") or []
    if tool_calls:
        ok, meta = SessionStore.enforce_tools(sid, len(tool_calls))
        if not ok:
            raise HTTPException(status_code=429, detail=meta)

    # Approx tokens for this turn: input + assistant content
    msg = _format_message_from_state(state)
    approx = _approx_tokens(body.message, msg["content"])
    ok, meta = SessionStore.enforce_tokens(sid, approx)
    if not ok:
        raise HTTPException(status_code=429, detail=meta)

    # --- Persist assistant turn in session memory ---
    SessionMemory.append(sid, role="assistant", content=msg["content"])

    # --- Return assistant payload (echo sessionId so UI can keep using it) ---
    return {**msg, "sessionId": sid}
