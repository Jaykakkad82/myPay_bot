# agent_multi/nodes/summarizer.py
from __future__ import annotations
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..prompts import SUMMARIZER_SYSTEM, OUT_OF_SCOPE_HELP
from ..utils.trace import push_trace

def summarize(state: Dict[str, Any], model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    push_trace(state, "summarize", "start")

    # If no steps were executed (noop/out-of-scope/greeting), return fixed help text.
    if not (state.get("plan") or []) or state.get("intent") == "noop":
        content = (state.get("result") or {}).get("summary") or OUT_OF_SCOPE_HELP
        out = {**state, "result": {"summary": content}, "status": state.get("status") or "OK"}
        push_trace(out, "summarize", "ok")
        return out

    # Otherwise, produce a short LLM summary of what the tools did.
    llm = ChatOpenAI(model=model_name, temperature=0)
    scratch = state.get("scratch") or {}
    prompt = ChatPromptTemplate.from_messages([
        ("system", SUMMARIZER_SYSTEM),
        ("human", "Summarize briefly what happened.\n\nScratch:\n{scratch}"),
    ])
    msg = prompt.format_messages(scratch=str(scratch)[:6000])
    text = llm.invoke(msg).content
    out = {**state, "result": {"summary": text}, "status": state.get("status") or "OK"}
    push_trace(out, "summarize", "ok")
    return out
