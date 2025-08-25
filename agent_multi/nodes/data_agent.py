from __future__ import annotations
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from ..prompts import DATA_SYSTEM
from ..tools_registry import build_read_only_tools
from ..utils.trace import push_trace, push_tool_call

# build once (full set of read-only tools)
_DATA_TOOLS = build_read_only_tools()

def _build_data_agent(model_name: str = "gpt-4o-mini") -> AgentExecutor:
    llm = ChatOpenAI(model=model_name, temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", DATA_SYSTEM),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm, _DATA_TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=_DATA_TOOLS,
        verbose=False,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        max_iterations=10,
    )

_data_agent = None

async def run_data_step(state: Dict[str, Any]) -> Dict[str, Any]:
    global _data_agent
    if _data_agent is None:
        _data_agent = _build_data_agent()

    push_trace(state, "data_agent", "start")

    step_idx = state.get("step_idx", 0)
    step = (state.get("plan") or [])[step_idx]
    operation = step.get("operation")
    args = step.get("args") or {}

    user_msg = f""" User message: {state.get("input", "")}
                Operation as per planner: {operation}
                Args: {args}
                Use the user message and planner's operation to Choose and CALL exactly one tool from the available tools. Return the JSON result.
                If the operation cannot be performed, return an empty JSON object {{}}."""

    print("Data agent user message: ", user_msg)
    res = await _data_agent.ainvoke({"input": user_msg, "chat_history": state.get("messages", [])})

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
    print("Data agent output state: ", new_state)
    return new_state
