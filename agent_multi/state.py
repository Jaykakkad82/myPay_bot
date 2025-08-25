from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, TypedDict
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

class GraphState(TypedDict, total=False):
    input: str
    messages: Annotated[List[Any], add_messages]

    intent: Optional[str]
    plan: List[Dict[str, Any]]
    step_idx: int

    scratch: Dict[str, Any]
    result: Any

    # compliance/approvals
    risk: Optional[str]
    status: Optional[Literal["OK", "AWAITING_APPROVAL", "DENIED"]]
    approval_id: Optional[str]
    approved: Optional[bool]

    # 👇 NEW: UI metadata
    trace: List[Dict[str, Any]]           # [{node, status, details?}]
    tool_calls: List[Dict[str, Any]]      # [{tool, args}]
    pending_approval: Optional[Dict[str, Any]]  # {reason, args}
