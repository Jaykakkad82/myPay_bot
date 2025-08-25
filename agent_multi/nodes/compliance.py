from __future__ import annotations
from typing import Dict, Any, List, Optional
from ..utils.trace import push_trace
import uuid
from ..workflow.approvals import ApprovalStore

# Names we consider "write" actions (support both tool and operation styles)
WRITE_TOOL_NAMES = {"make_payment", "create_transaction", "create_customer"}
WRITE_OPS = {"payments.make", "transactions.create", "customers.create"}

def _step_name(step: Dict[str, Any]) -> str:
    """Human-friendly name for tracing: prefer tool, else operation, else 'unknown'."""
    return (step.get("tool")
            or step.get("operation")
            or "unknown")

def _is_write(step: Dict[str, Any]) -> bool:
    """Decide if the step is a write action."""
    # agent="execution" is a strong signal
    if step.get("agent") == "execution":
        return True
    tool = step.get("tool")
    if tool in WRITE_TOOL_NAMES:
        return True
    op = step.get("operation")
    if op in WRITE_OPS:
        return True
    return False

def _needs_payment_args(args: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    if not args.get("transactionId"): missing.append("transactionId")
    if not args.get("method"): missing.append("method")
    if not args.get("idempotencyKey"): missing.append("idempotencyKey")
    return missing

def _is_high_value(amount: Optional[float]) -> bool:
    try:
        return amount is not None and float(amount) >= 10.0
    except Exception:
        return False

def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    """Gate risky writes; be tolerant to plan steps that use 'tool' or 'operation'."""
    push_trace(state, "compliance", "start")

    plan = state.get("plan") or []
    idx = state.get("step_idx", 0)
    if not plan or idx >= len(plan):
        out = {**state, "status": "OK"}
        push_trace(out, "compliance", "skipped", {"reason": "no_step"})
        return out

    step = plan[idx] or {}
    args: Dict[str, Any] = step.get("args") or {}
    name = _step_name(step)
    risk_reasons: List[str] = []

    if _is_write(step):
        # Tool/operation specific checks
        if name in ("make_payment", "payments.make"):
            missing = _needs_payment_args(args)
            if missing:
                risk_reasons.append(f"payment missing required: {', '.join(missing)}")

        if name in ("create_transaction", "transactions.create"):
            amt = args.get("amount")
            try:
                if amt is None or float(amt) <= 0:
                    risk_reasons.append("invalid or non-positive amount for transaction")
                elif _is_high_value(float(amt)):
                    risk_reasons.append("high-value transaction requires approval")
            except Exception:
                risk_reasons.append("amount not parseable")

    # If nothing risky → allow
    if not risk_reasons:
        out = {**state, "status": "OK"}
        push_trace(out, "compliance", "ok", {"step": name, "args": args})
        return out

    # If already approved, pass through
    if state.get("approved") is True:
        out = {**state, "status": "OK"}
        push_trace(out, "compliance", "ok", {"step": name, "approved": True})
        return out

    # Otherwise surface an approval banner
    approval_id = state.get("approval_id") or str(uuid.uuid4())
    pending = {
        "reason": "; ".join(risk_reasons),
        "args": args,
        "approval_id": approval_id,
    }
    out = {
        **state,
        "status": "AWAITING_APPROVAL",
        "approval_id": approval_id,
        "pending_approval": pending,
    }
    ApprovalStore.upsert(approval_id, {"state": out})
    push_trace(out, "compliance", "needs_approval", {"reasons": risk_reasons, "step": name})
    return out