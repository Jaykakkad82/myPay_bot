# agent_multi/nodes/notifier.py
from __future__ import annotations
import os, ssl, smtplib, time
from email.message import EmailMessage
from datetime import datetime, timezone
from typing import Dict, Any
from ..utils.trace import push_trace

def _smtp_config() -> Dict[str, Any]:
    return {
        "host": os.getenv("SMTP_HOST", "email-smtp.us-east-1.amazonaws.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),          # 587/2587 = STARTTLS, 465 = SSL
        "user": os.getenv("SMTP_USERNAME", ""),              # SES SMTP user – NOT AWS access key
        "password": os.getenv("SMTP_PASSWORD", ""),          # SES SMTP password
        "from_email": os.getenv("SMTP_FROM", "jay.kakkad@gmail.com"),
        "default_to": os.getenv("SMTP_TO_DEFAULT", "jay.kakkad@gmail.com"),
        "debug": int(os.getenv("SMTP_DEBUG", "0")),          # set 1 to see SMTP conversation in logs
    }

def _last_write_kind(state: Dict[str, Any]):
    """Return ('payment'|'transaction'|None, payload_dict|None) based on execution agent output."""
    data = state.get("data") or {}
    if isinstance(data.get("payment"), dict):
        return "payment", data["payment"]
    if isinstance(data.get("transaction"), dict):
        return "transaction", data["transaction"]
    # Fallback: if execution returned a dict result directly, try to infer
    out = state.get("result")
    if isinstance(out, dict) and ("transactionId" in out or "id" in out):
        # Heuristic
        if "amount" in out and "currency" in out and "customerId" in out:
            return "transaction", out
    return None, None

def _compose_email(kind: str, obj: Dict[str, Any]) -> Dict[str, str]:
    if kind == "payment":
        subject = f"Payment receipt #{obj.get('id')}"
        text = (
            f"Status: {obj.get('status')}\n"
            f"Amount: {obj.get('amount')} {obj.get('currency')}\n"
            f"Transaction ID: {obj.get('transactionId')}"
        )
    else:
        subject = f"Transaction created #{obj.get('id')}"
        text = (
            f"Customer: {obj.get('customerId')}\n"
            f"Amount: {obj.get('amount')} {obj.get('currency')}\n"
            f"Category: {obj.get('category')}\n"
            f"Description: {obj.get('description')}"
        )
    return {"subject": subject, "text": text}

def _send_email(cfg: Dict[str, Any], to_addr: str, subject: str, body_text: str) -> int:
    """
    Returns elapsed ms. Raises on SMTP errors (caught by caller).
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["from_email"]     # MUST be a SES-verified identity
    msg["To"] = to_addr
    msg.set_content(body_text)

    t0 = time.perf_counter()
    port = cfg["port"]
    host = cfg["host"]
    context = ssl.create_default_context()

    if port == 465:
        server = smtplib.SMTP_SSL(host, port, context=context)
    else:
        server = smtplib.SMTP(host, port)
        if cfg["debug"]:
            server.set_debuglevel(1)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()

    try:
        server.login(cfg["user"], cfg["password"])  # AUTH must come after STARTTLS on 587/2587
        server.send_message(msg)
    finally:
        server.quit()

    return int((time.perf_counter() - t0) * 1000)

def notify(state: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _smtp_config()
    kind, obj = _last_write_kind(state)

    # Nothing to notify about
    if not kind or not isinstance(obj, dict):
        push_trace(state, "notifier", "ok", {"count": len(state.get("notifications", [])), "ms": 0})
        return state

    # Decide recipient (prefer payload/customer email; fall back to default)
    to_addr = (
        obj.get("customerEmail")
        or (state.get("extras") or {}).get("email")
        or cfg["default_to"]
    )

    payload = _compose_email(kind, obj)
    state.setdefault("notifications", [])

    try:
        ms = _send_email(cfg, to_addr, payload["subject"], payload["text"])
        state["notifications"].append({
            "type": "email",
            "provider": "ses-smtp",
            "to": to_addr,
            "subject": payload["subject"],
            "preview": payload["text"].splitlines()[0] if payload["text"] else "",
            "status": "SENT",
            "ms": ms,
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "meta": {"kind": kind, "id": obj.get("id")},
        })
        push_trace(state, "notifier", "ok", {"count": len(state["notifications"]), "ms": ms})
    except Exception as e:
        state["notifications"].append({
            "type": "email",
            "provider": "ses-smtp",
            "to": to_addr,
            "subject": payload["subject"],
            "preview": payload["text"].splitlines()[0] if payload["text"] else "",
            "status": "ERROR",
            "error": str(e),
            "ms": 0,
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "meta": {"kind": kind, "id": obj.get("id")},
        })
        push_trace(state, "notifier", "error", {"error": str(e)})

    return state
