# agent_multi/workflow/graph.py
from __future__ import annotations
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from ..state import GraphState
from ..nodes.orchestrator import orchestrate
from ..nodes.data_agent import run_data_step
from ..nodes.compliance import compliance_check
from ..nodes.execution_agent import run_exec_step
from ..nodes.summarizer import summarize
from ..nodes.notifier import notify

def _has_more_steps(state: Dict[str, Any]) -> bool:
    return state.get("step_idx", 0) < len(state.get("plan") or [])

def _route_next(state: Dict[str, Any]) -> str:
    if not _has_more_steps(state):
        return "summarize"
    step = (state.get("plan") or [])[state["step_idx"]]
    agent = step.get("agent")
    if agent == "data":
        return "data_agent"
    elif agent == "execution":
        return "compliance"
    return "summarize"

def _is_write_step(step: dict) -> bool:
    name = (step.get("operation") or step.get("tool") or "").lower()
    return any(k in name for k in [
        "transactions.create", "create_transaction",
        "payments.make", "make_payment",
    ])

def _execution_router(state: Dict[str, Any]) -> str:
    step_idx = state.get("step_idx", 0)
    plan = state.get("plan") or []
    # If just finished a write step, go to notifier
    if step_idx > 0 and step_idx <= len(plan):
        prev_step = plan[step_idx - 1]
        if prev_step.get("agent") == "execution" and _is_write_step(prev_step):
            return "notifier"
    # Otherwise, route as usual
    if not _has_more_steps(state):
        return "summarize"
    step = plan[step_idx] if step_idx < len(plan) else {}
    agent = step.get("agent")
    if agent == "data":
        return "data_agent"
    elif agent == "execution":
        return "compliance"
    return "summarize"

def _approved(state: Dict[str, Any]) -> bool:
    return state.get("status") == "OK"

def build_multi_agent_graph():
    g = StateGraph(GraphState)

    # nodes
    g.add_node("orchestrator", orchestrate)
    g.add_node("data_agent", run_data_step)
    g.add_node("compliance", compliance_check)
    g.add_node("execution", run_exec_step)
    g.add_node("notifier", notify)
    g.add_node("summarize", summarize)

    # entry
    g.set_entry_point("orchestrator")

    # router after orchestrator and after each step
    g.add_conditional_edges("orchestrator", _route_next, {
        "data_agent": "data_agent",
        "compliance": "compliance",
        "summarize": "summarize",
    })
    # data step → route again
    g.add_conditional_edges("data_agent", _route_next, {
        "data_agent": "data_agent",
        "compliance": "compliance",
        "summarize": "summarize",
    })


    # compliance gate for execution
    def _compliance_out(state: Dict[str, Any]) -> str:
        if state.get("status") == "AWAITING_APPROVAL":
            return "summarize"  # stop here; caller should resume after approval
        return "execution"

    g.add_conditional_edges("compliance", _compliance_out, {
        "execution": "execution",
        "summarize": "summarize",
    })

    # after execution → route again

    g.add_conditional_edges("execution", _execution_router, {
    "notifier": "notifier",
    "data_agent": "data_agent",
    "compliance": "compliance",
    "summarize": "summarize",
    })

    g.add_edge("notifier", "summarize")


    # summarize → END
    g.add_edge("summarize", END)

    return g.compile()
