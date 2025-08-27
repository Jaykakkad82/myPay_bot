from __future__ import annotations
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from ..prompts import DATA_SYSTEM
from ..tools_registry import build_read_only_tools
from ..utils.trace import push_trace, push_tool_call

# ---------- tools & routing ----------
_DATA_TOOLS = build_read_only_tools()
_TOOL_BY_NAME = {t.name: t for t in _DATA_TOOLS}

_OP_CANDIDATES: Dict[str, List[str]] = {
    "customers.get":      ["get_customer"],
    "transactions.list":  ["search_transactions"],
    "transactions.get":   ["get_transaction_detail"],
    "analytics.spend":    ["spend_summary"],
    "analytics.category": ["spend_by_category"],
    "payments.get":       ["get_payment"],
}

def _tools_for_operation(op: str):
    names = _OP_CANDIDATES.get(op) or []
    tools = [_TOOL_BY_NAME[n] for n in names if n in _TOOL_BY_NAME]
    return tools or list(_DATA_TOOLS)

# ---------- helpers ----------
def _escape_braces(s: str) -> str:
    """Escape { and } for use inside ChatPromptTemplate literal strings."""
    return s.replace("{", "{{").replace("}", "}}")

def _coerce_history(raw) -> List[BaseMessage]:
    """Convert saved history (dicts or BaseMessages) into LangChain messages."""
    msgs: List[BaseMessage] = []
    for m in raw or []:
        if isinstance(m, BaseMessage):
            msgs.append(m)
            continue
        if isinstance(m, dict):
            role = (m.get("role") or "").lower()
            content = str(m.get("content") or "")
            if role == "assistant":
                msgs.append(AIMessage(content=content))
            elif role == "system":
                msgs.append(SystemMessage(content=content))
            else:
                msgs.append(HumanMessage(content=content))
            continue
        msgs.append(HumanMessage(content=str(m)))
    return msgs

def _build_llm_agent(allowed_tools, model_name: str = "gpt-4o-mini") -> AgentExecutor:
    llm = ChatOpenAI(model=model_name, temperature=0)

    # Escape EVERYTHING that goes into a template literal
    safe_system = _escape_braces(DATA_SYSTEM)

    inv_lines = [f"- {_escape_braces(t.name)}: {_escape_braces(t.description or '')}"
                 for t in allowed_tools]
    inventory = "\n".join(inv_lines)

    # Write rules naturally then escape
    rules_text = (
        "\n\nRules:\n"
        "- Use exactly ONE tool.\n"
        "- Prefer tools aligned with the planner's operation.\n"
        "- If you cannot perform the operation, return {}."
    )
    rules = _escape_braces(rules_text)

    prompt = ChatPromptTemplate.from_messages([
        ("system", safe_system + "\n\nAvailable tools:\n" + inventory + rules),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, allowed_tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=allowed_tools,
        verbose=False,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        max_iterations=20,  # single tool call for read steps
    )

# ---------- main ----------
async def run_data_step(state: Dict[str, Any]) -> Dict[str, Any]:
    push_trace(state, "data_agent", "start")

    plan = state.get("plan") or []
    step_idx = int(state.get("step_idx", 0))
    step = plan[step_idx] if step_idx < len(plan) else {}

    operation = (step.get("operation") or step.get("tool") or "").strip()
    args = step.get("args") or {}

    allowed_tools = _tools_for_operation(operation)
    agent = _build_llm_agent(allowed_tools)

    user_text = state.get("input", "")
    # NOTE: This string is passed as the value of {input}; braces here are SAFE.
    user_msg = (
        f"User message: {user_text}\n"
        f"Planner operation: {operation}\n"
        f"Planner args: {args}\n\n"
        "Choose and Call one tool based on operations and args provided. Return the tool's raw JSON result. "
        "If you cannot perform the operation (missing args / no matching tool), return {}."
    )

    chat_history = _coerce_history(state.get("messages", []))
    res = await agent.ainvoke({"input": user_msg, "chat_history": chat_history})

    chosen: List[str] = []
    for action, _obs in res.get("intermediate_steps", []):
        try:
            push_tool_call(state, action.tool, action.tool_input)
            chosen.append(action.tool)
        except Exception:
            pass

    if not chosen:
        push_trace(state, "data_agent", "warning", {"reason": "no_tool_called_for_operation", "operation": operation})

    output = res.get("output", res)
    print(output)

    # Update scratch & step
    scratch = dict(state.get("scratch") or {})
    scratch_key = f"step_{step_idx}_{operation or 'noop'}"
    scratch[scratch_key] = output
    scratch["last_result"] = output

    new_state = {**state, "scratch": scratch, "result": output, "step_idx": step_idx + 1}
    push_trace(new_state, "data_agent", "ok", {"operation": operation, "chosen_tools": chosen})
    return new_state
