# agent_multi/workflow/sessions.py
from __future__ import annotations
from typing import Dict, Any, List

class SessionMemory:
    _mem: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get(cls, sid: str) -> Dict[str, Any]:
        if sid not in cls._mem:
            cls._mem[sid] = {"messages": [], "scratch": {}}
        return cls._mem[sid]

    @classmethod
    def append(cls, sid: str, role: str, content: str) -> None:
        m = cls.get(sid)["messages"]
        m.append({"role": role, "content": content})
        # keep last ~20 messages
        if len(m) > 20:
            cls._mem[sid]["messages"] = m[-20:]

    @classmethod
    def put_scratch(cls, sid: str, key: str, value: Any) -> None:
        cls.get(sid)["scratch"][key] = value

    @classmethod
    def get_messages(cls, sid: str) -> List[Dict[str, str]]:
        return list(cls.get(sid)["messages"])

    @classmethod
    def get_scratch(cls, sid: str) -> Dict[str, Any]:
        return dict(cls.get(sid)["scratch"])
