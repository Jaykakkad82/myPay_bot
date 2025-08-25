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

def _approved(state: Dict[str, Any]) -> bool:
    return state.get("status") == "OK"

def build_multi_agent_graph():
    g = StateGraph(GraphState)

    # nodes
    g.add_node("orchestrator", orchestrate)
    g.add_node("data_agent", run_data_step)
    g.add_node("compliance", compliance_check)
    g.add_node("execution", run_exec_step)
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
    g.add_conditional_edges("execution", _route_next, {
        "data_agent": "data_agent",
        "compliance": "compliance",
        "summarize": "summarize",
    })

    # summarize → END
    g.add_edge("summarize", END)

    return g.compile()
