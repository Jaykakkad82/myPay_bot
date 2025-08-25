# agent_multi/routes/approval.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, timezone
import uuid

from ..workflow.graph import build_multi_agent_graph
from ..workflow.approvals import ApprovalStore

graph = build_multi_agent_graph()
router = APIRouter()

class ApprovalIn(BaseModel):
    approvalId: str
    decision: str  # "APPROVE" | "DENY"
    # client should send last known state if you want pure stateless resume;
    # or you can persist state server-side keyed by sessionId.
    lastState: dict | None = None

def _format_msg(state: Dict[str, Any]) -> Dict[str, Any]:
    content = state.get("result", {}).get("summary") or "Action handled."
    return {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": content,
        "trace": state.get("trace") or [],
        "tool_calls": state.get("tool_calls") or [],
        "pending_approval": None if state.get("status") == "OK" else state.get("pending_approval"),
        "ts": datetime.now(tz=timezone.utc).isoformat(),
    }

@router.post("/workflow/approval")
async def approval(body: ApprovalIn):
    rec = ApprovalStore.get(body.approvalId)
    if not rec and not body.lastState:
        raise HTTPException(status_code=454, detail="approval not found")

    if body.decision.upper() == "APPROVE":
        ApprovalStore.approve(body.approvalId)
        # Resume: mark approved=True and continue at same step
        resumed = {
            **body.lastState,
            "approved": True,
            "status": "OK",
            "trace": body.lastState.get("trace") or [],
            "tool_calls": body.lastState.get("tool_calls") or [],
        }
        state = await graph.ainvoke(resumed)
        return _format_msg(state)
    else:
        ApprovalStore.deny(body.approvalId)
        # Deny: short message; you could also set status=DENIED
        
        return {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": "Request denied.",
            "trace": (body.lastState.get("trace") or []) + [{"node": "approval", "status": "denied"}],
            "tool_calls": body.lastState.get("tool_calls") or [],
            "pending_approval": None,
            "ts": datetime.now(tz=timezone.utc).isoformat(),
        }
