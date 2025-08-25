# agent_multi/workflow/approvals.py
from __future__ import annotations
from typing import Dict, Any

class ApprovalStore:
    _store: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def upsert(cls, approval_id: str, payload: Dict[str, Any]) -> None:
        cls._store[approval_id] = {"status": "PENDING", **payload}

    @classmethod
    def approve(cls, approval_id: str) -> None:
        if approval_id in cls._store:
            cls._store[approval_id]["status"] = "APPROVED"

    @classmethod
    def deny(cls, approval_id: str) -> None:
        if approval_id in cls._store:
            cls._store[approval_id]["status"] = "DENIED"

    @classmethod
    def get(cls, approval_id: str) -> Dict[str, Any] | None:
        return cls._store.get(approval_id)
