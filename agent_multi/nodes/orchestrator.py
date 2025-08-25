from __future__ import annotations
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..prompts import ORCH_SYSTEM, OUT_OF_SCOPE_HELP
from ..utils.trace import push_trace

NOOP_INTENT = "noop"

def orchestrate(state: Dict[str, Any], model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    push_trace(state, "orchestrator", "start", {"input": state.get("input", "")})
    user_input = (state.get("input") or "").strip()
    if not user_input:
        out_state = {**state, "intent": NOOP_INTENT, "plan": [], "step_idx": 0, "status": "OK",
                     "result": {"summary": OUT_OF_SCOPE_HELP}}
        push_trace(out_state, "orchestrator", "ok", {"intent": NOOP_INTENT, "steps": 0})
        return out_state

    llm = ChatOpenAI(model=model_name, temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "{sys}"),
        ("human", "{query}"),
    ])
    msg = prompt.format_messages(sys=ORCH_SYSTEM, query=user_input)
    out = llm.invoke(msg).content

    # Parse -> keep 'operation' only
    intent, plan = NOOP_INTENT, []
    try:
        obj = json.loads(out)
        intent = obj.get("intent") or NOOP_INTENT
        raw = obj.get("plan") or []
        norm = []
        for step in raw:
            agent = step.get("agent")
            op = step.get("operation")
            args = step.get("args") or {}
            if agent in ("data", "execution") and isinstance(op, str):
                norm.append({"agent": agent, "operation": op, "args": args})
        plan = norm
    except Exception:
        intent, plan = NOOP_INTENT, []

    if intent == NOOP_INTENT or not plan:
        out_state = {**state, "intent": NOOP_INTENT, "plan": [], "step_idx": 0, "status": "OK",
                     "result": {"summary": OUT_OF_SCOPE_HELP}}
        push_trace(out_state, "orchestrator", "ok", {"intent": NOOP_INTENT, "steps": 0})
        return out_state

    out_state = {**state, "intent": intent, "plan": plan, "step_idx": 0, "status": "OK"}
    # 👇 show full plan in chip so you can compare later
    push_trace(out_state, "orchestrator", "ok", {"intent": intent, "steps": len(plan), "plan": plan})
    return out_state
