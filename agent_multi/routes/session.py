# agent_multi/routes/session.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from ..runtime.session_store import SessionStore

router = APIRouter()

class StartOut(BaseModel):
    sessionId: str
    tier: str
    limits: dict

@router.post("/session/start", response_model=StartOut)
async def start(request: Request):
    ip = request.client.host if request.client else ""
    ua = request.headers.get("user-agent", "")
    sess = SessionStore.start_session(ip, ua)
    return {"sessionId": sess["sessionId"], "tier": sess["tier"], "limits": sess["limits"]}

class UpgradeIn(BaseModel):
    sessionId: str
    accessKey: str

@router.post("/session/upgrade")
async def upgrade(body: UpgradeIn):
    try:
        attrs, tier = SessionStore.upgrade(body.sessionId, body.accessKey)
        return {"sessionId": body.sessionId, "tier": tier, "limits": attrs["limits"]}
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid access key")

class LimitsOut(BaseModel):
    sessionId: str
    tier: str
    limits: dict

@router.get("/session/limits", response_model=LimitsOut)
async def limits(sessionId: str):
    s = SessionStore.get_session(sessionId)
    if not s: raise HTTPException(status_code=404, detail="unknown session")
    return {"sessionId": s["sessionId"], "tier": s["tier"], "limits": s["limits"]}
