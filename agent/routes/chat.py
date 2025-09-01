from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage

from ..agent_builder import build_agent
from ..utils.guards import is_in_scope
from ..prompts import REFUSAL
from ..session_store import SESSION_HISTORY

router = APIRouter()

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    # (optional) keep your hints
    customerId: Optional[int] = None
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    currency: Optional[str] = None
    # NEW: identify the conversation
    sessionId: Optional[str] = Field(default="default")

class ChatResponse(BaseModel):
    answer: str

def get_agent():
    # You can switch this to a singleton if you prefer.
    return build_agent()

@router.post("/chat")
async def chat(req: ChatRequest, agent=Depends(get_agent)):
    if not is_in_scope(req.message):
        return { "content": REFUSAL }

    # (Optional) Inline context hint
    context = f"(Context: customerId={req.customerId}) " if req.customerId else ""
    final_prompt = f"{context}{req.message}"

    # Pull prior history for this session
    history = SESSION_HISTORY[req.sessionId]

    # Invoke agent with history
    result = await agent.ainvoke({
        "input": final_prompt,
        "chat_history": history  # must match MessagesPlaceholder("chat_history") in your prompt
    })

    answer = (result.get("output") or "").strip()
    if not answer:
        raise HTTPException(status_code=500, detail="Empty agent answer")

    # Append this turn to history
    history.append(HumanMessage(content=req.message))
    history.append(AIMessage(content=answer))

    return { "content": answer}

# ChatResponse(answer=answer)
