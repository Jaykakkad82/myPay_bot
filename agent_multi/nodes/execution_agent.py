# agent_multi/nodes/execution_agent.py
from __future__ import annotations
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
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

_exec_agent = None

# 👇 async
async def run_exec_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the current plan step (write action). Assumes compliance has passed."""
    global _exec_agent
    if _exec_agent is None:
        _exec_agent = _build_exec_agent()

    push_trace(state, "execution", "start")

    step_idx = state.get("step_idx", 0)
    step = (state.get("plan") or [])[step_idx]
    operation = step.get("operation")
    args = dict(step.get("args") or {})

    

    # placeholder propagation & idempotency
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

    user_msg = f""" User message: {state.get("input", "")}
                Operation as per planner: {operation}
                Args: {args}
                Use the user message and planner's operation to Choose and CALL exactly one tool from the available tools. Return the JSON result.
                If the operation cannot be performed, return an empty JSON object {{}}."""

    # 👇 async invoke
    res = await _exec_agent.ainvoke({"input": user_msg, "chat_history": state.get("messages", [])})

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

    scratch = dict(state.get("scratch") or {})
    scratch_key = f"step_{step_idx}_{operation}"
    scratch[scratch_key] = output
    scratch["last_result"] = output

    new_state = {**state, "scratch": scratch, "result": output, "step_idx": step_idx + 1}
    push_trace(new_state, "data_agent", "ok", {"operation": operation, "chosen_tools": chosen})
    return new_state
