# agent_multi/nodes/orchestrator.py
from __future__ import annotations
import json
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
# Optional: import types for isinstance checks (keeps it robust)
try:
    from langchain_core.messages import BaseMessage
except Exception:  # if the import isn’t available at runtime
    BaseMessage = tuple()  # harmless sentinel

from ..prompts import ORCH_SYSTEM, OUT_OF_SCOPE_HELP
from ..utils.trace import push_trace

def _coerce_msg(m) -> tuple[str, str]:
    """
    Return (role, content) from either a dict-like item or a LangChain Message.
    Falls back to ('user', str(m)) if unknown.
    """
    # dict-like
    if isinstance(m, dict):
        role = (m.get("role") or "").lower().strip()
        content = str(m.get("content") or "")
        if role in ("user", "assistant", "system"):
            return role, content
        # fallback if role is missing
        return "user", content

    # LangChain Message
    if BaseMessage and isinstance(m, BaseMessage):
        t = getattr(m, "type", "") or ""
        content = str(getattr(m, "content", "") or "")
        role = (
            "user" if t in ("human", "user") else
            "assistant" if t in ("ai", "assistant") else
            "system" if t == "system" else
            "user"
        )
        return role, content

    # Fallback
    return "user", str(m)

def _render_history(messages: List[Any], limit: int = 8) -> str:
    if not messages:
        return ""
    lines: List[str] = []
    for m in messages[-limit:]:
        role, content = _coerce_msg(m)
        if not content:
            continue
        tag = "User" if role == "user" else ("Assistant" if role == "assistant" else "System")
        lines.append(f"{tag}: {content}")
    return "\n".join(lines)

NOOP_INTENT = "noop"

def orchestrate(state: Dict[str, Any], model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    push_trace(state, "orchestrator", "start", {"input": state.get("input", "")})
    user_input = (state.get("input") or "").strip()
    chat_history = state.get("messages") or []
    history_txt = _render_history(chat_history)

    if not user_input:
        out_state = {**state, "intent": NOOP_INTENT, "plan": [], "step_idx": 0, "status": "OK",
                     "result": {"summary": OUT_OF_SCOPE_HELP}}
        push_trace(out_state, "orchestrator", "ok", {"intent": NOOP_INTENT, "steps": 0})
        return out_state

    llm = ChatOpenAI(model=model_name, temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "{sys}"),
        ("system", "Conversation so far:\n{history}"),
        ("human", "{query}"),
    ])
    msg = prompt.format_messages(sys=ORCH_SYSTEM, history=history_txt, query=user_input)
    raw = llm.invoke(msg).content

    intent, plan = NOOP_INTENT, []
    try:
        obj = json.loads(raw)
        intent = obj.get("intent") or NOOP_INTENT
        raw_steps = obj.get("plan") or []
        norm = []
        for step in raw_steps:
            agent = step.get("agent")
            op = step.get("operation") or step.get("tool")
            args = step.get("args") or {}
            if agent in ("data", "execution") and isinstance(op, str):
                # preserve whichever key style you use
                if "operation" in step:
                    norm.append({"agent": agent, "operation": op, "args": args})
                else:
                    norm.append({"agent": agent, "tool": op, "args": args})
        plan = norm
    except Exception:
        intent, plan = NOOP_INTENT, []

    if intent == NOOP_INTENT or not plan:
        out_state = {**state, "intent": NOOP_INTENT, "plan": [], "step_idx": 0, "status": "OK",
                     "result": {"summary": OUT_OF_SCOPE_HELP}}
        push_trace(out_state, "orchestrator", "ok", {"intent": NOOP_INTENT, "steps": 0})
        return out_state

    out_state = {**state, "intent": intent, "plan": plan, "step_idx": 0, "status": "OK"}
    push_trace(out_state, "orchestrator", "ok", {"intent": intent, "steps": len(plan), "plan": plan})
    return out_state
