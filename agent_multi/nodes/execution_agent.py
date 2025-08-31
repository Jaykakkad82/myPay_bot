# agent_multi/nodes/execution_agent.py
from __future__ import annotations
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent_multi import state
from ..prompts import EXEC_SYSTEM
from ..tools_registry import build_write_tools
from ..utils.trace import push_trace, push_tool_call

WRITE_OPS = {"payments.make", "transactions.create", "customers.create"}

def _build_exec_agent(model_name: str = "gpt-4o-mini") -> AgentExecutor:
    tools = build_write_tools()
    llm = ChatOpenAI(model=model_name, temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", EXEC_SYSTEM),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )

def _coerce_output_from_agent(res: Dict[str, Any]):
    """Prefer the last tool observation; fall back to JSON in text; else raw text."""
    last_obs = None
    for _action, obs in res.get("intermediate_steps", []):
        if obs is not None:
            last_obs = obs
    if isinstance(last_obs, (dict, list)):
        return last_obs

    # Try to pull JSON out of the LLM text if present
    txt = res.get("output", "")
    if isinstance(txt, str):
        try:
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", txt)
            if m:
                return json.loads(m.group(1))
        except Exception:
            pass
    return txt  # give back the text as a last resort

_exec_agent = None


async def run_exec_step(state: Dict[str, Any]) -> Dict[str, Any]:
    global _exec_agent
    if _exec_agent is None:
        _exec_agent = _build_exec_agent()

    push_trace(state, "execution", "start")

    step_idx = state.get("step_idx", 0)
    step = (state.get("plan") or [])[step_idx]
    operation = step.get("operation")
    args = dict(step.get("args") or {})

    # ---- id/placeholder/idempotency handling (unchanged) ----
    last = (state.get("scratch") or {}).get("last_result")
    def _maybe_replace(v):
        if isinstance(v, str) and v.upper().startswith("{{TRANSACTION_ID_FROM_PREV"):
            if isinstance(last, dict):
                cand = last.get("id") or last.get("transactionId") or last.get("data", {}).get("id")
                if cand:
                    return cand
        return v
    for k, v in list(args.items()):
        args[k] = _maybe_replace(v)
    if operation in WRITE_OPS and not args.get("idempotencyKey"):
        args["idempotencyKey"] = f"pay-{step_idx}-auto"

    user_msg = (
        f"User message: {state.get('input','')}\n"
        f"Planner operation: {operation}\n"
        f"Planner args: {args}\n\n"
        "Choose and CALL exactly one tool. Return the tool's raw JSON result. "
        "If you cannot perform the operation, return {}."
    )

    res = await _exec_agent.ainvoke({"input": user_msg, "chat_history": state.get("messages", [])})

    chosen: List[str] = []
    last_obs = None
    for action, obs in res.get("intermediate_steps", []):
        try:
            push_tool_call(state, action.tool, action.tool_input)
            chosen.append(action.tool)
            last_obs = obs
        except Exception:
            pass
    if not chosen:
        push_trace(state, "execution", "warning", {"reason": "no_tool_called_for_operation", "operation": operation})

    # 👇 prefer the tool observation
    output = last_obs if last_obs is not None else _coerce_output_from_agent(res)

    # keep scratch
    scratch = dict(state.get("scratch") or {})
    scratch_key = f"step_{step_idx}_{operation}"
    scratch[scratch_key] = output
    scratch["last_result"] = output

    # populate state["data"] so notifier can see it
    kind = (operation or step.get("tool") or "").lower()
    data = dict(state.get("data") or {})
    if "payments.make" in kind or "make_payment" in kind:
        data["payment"] = output if isinstance(output, dict) else {"result": output}
    elif "transactions.create" in kind or "create_transaction" in kind:
        data["transaction"] = output if isinstance(output, dict) else {"result": output}

    new_state = {**state, "scratch": scratch, "data": data, "result": output, "step_idx": step_idx + 1}
    push_trace(new_state, "execution", "ok", {"operation": operation, "chosen_tools": chosen, "output_type": type(output).__name__})
    return new_state