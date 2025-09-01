# agent_multi/routes/approval.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from fastapi.encoders import jsonable_encoder

from ..workflow.graph import build_multi_agent_graph
from ..workflow.approvals import ApprovalStore

graph = build_multi_agent_graph()
router = APIRouter()

class ApprovalIn(BaseModel):
    approvalId: str
    decision: str  # "APPROVE" | "DENY"
    lastState: Optional[dict] = None  # client-provided last known graph state

def _format_msg(state: Dict[str, Any]) -> Dict[str, Any]:
    result = state.get("result")
    if isinstance(result, dict) and "summary" in result:
        content = result["summary"]
    else:
        content = f"Action handled.\n\n```json\n{jsonable_encoder(result)}\n```"

    pending = None if state.get("status") == "OK" else state.get("pending_approval")
    return {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": content,
        "trace": state.get("trace") or [],
        "tool_calls": state.get("tool_calls") or [],
        "pending_approval": pending,
        "notifications": state.get("notifications") or [],
        "ts": datetime.now(tz=timezone.utc).isoformat(),
    }

@router.post("/workflow/approval")
async def approval(body: ApprovalIn):
    # 1) Look up approval record
    rec = ApprovalStore.get(body.approvalId)

    # 2) Determine the last state to resume with:
    #    prefer client-sent lastState; fall back to store (if you saved it there).
    last_state = body.lastState or (rec.get("state") if rec else None)
    if not rec and not last_state:
        # approval id unknown AND no state to resume -> 404
        raise HTTPException(status_code=404, detail="approval not found")
    if not last_state:
        # approval exists but we weren't given state and none is stored -> 400
        raise HTTPException(status_code=400, detail="missing lastState for resume")

    decision = (body.decision or "").strip().upper()
    if decision == "APPROVE":
        ApprovalStore.approve(body.approvalId)
        # Resume: mark approved=True so the compliance gate passes and continue the plan
        resumed = {
            **last_state,
            "approved": True,
            "status": "OK",
            # keep trace/tool_calls growing rather than losing them
            "trace": (last_state.get("trace") or []),
            "tool_calls": (last_state.get("tool_calls") or []),
        }
        state = await graph.ainvoke(resumed)
        return _format_msg(state)

    elif decision == "DENY":
        ApprovalStore.deny(body.approvalId)
        # Short deny message; preserve trace/tool_calls if present
        trace = (last_state.get("trace") or []) + [{"node": "approval", "status": "denied"}]
        return {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": "Request denied.",
            "trace": trace,
            "tool_calls": last_state.get("tool_calls") or [],
            "pending_approval": None,
            "notifications": last_state.get("notifications") or [],
            "ts": datetime.now(tz=timezone.utc).isoformat(),
        }

    else:
        raise HTTPException(status_code=400, detail="invalid decision; use APPROVE or DENY")
