from typing import Dict, Any
from ..utils.trace import push_trace

def notify(state: Dict[str, Any]) -> Dict[str, Any]:
    """Stub: in real world, call SendGrid/SMTP/Slack here."""
    # Example trigger: notify on payment success
    p = state.get("data", {}).get("payment")
    if p:
        # Compose an email payload; store for UI
        note = {
            "type": "email",
            "to": "demo-inbox@example.com",
            "subject": f"Payment receipt #{p.get('id')}",
            "body": f"Payment {p.get('status')} for {p.get('amount')} {p.get('currency')} (tx {p.get('transactionId')})."
        }
        state.setdefault("notifications", []).append(note)

    push_trace(state, "notifier", "ok", {"count": len(state.get("notifications", []))})
    return state
