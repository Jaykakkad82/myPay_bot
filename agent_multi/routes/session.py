# agent_multi/routes/session.py
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
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
    print(f"Started session {sess['sessionId']} from {ip} / {ua}")
    return {"sessionId": sess["sessionId"], "tier": sess["tier"], "limits": sess["limits"]}

# class UpgradeIn(BaseModel):
#     sessionId: str
#     accessKey: str

# @router.post("/session/upgrade")
# async def upgrade(body: UpgradeIn):
#     try:
#         attrs, tier = SessionStore.upgrade(body.sessionId, body.accessKey)
#         return {"sessionId": body.sessionId, "tier": tier, "limits": attrs["limits"]}
#     except ValueError:
#         raise HTTPException(status_code=400, detail="invalid access key")
    
@router.post("/session/upgrade")
async def upgrade(
    request: Request,
    sessionId: Optional[str] = None,  # query param is optional now
    x_session_id: Optional[str] = Header(default=None, convert_underscores=False),  # reads "X-Session-Id"
):
    sid = x_session_id or request.headers.get("X-Session-Id") or sessionId
    if not sid:
        raise HTTPException(status_code=401, detail="missing sessionId")
    
    body = await request.json()
    access_key = (body or {}).get("accessKey")
    if not access_key:
        raise HTTPException(status_code=400, detail="missing accessKey")
    
    try:
        attrs, tier = SessionStore.upgrade(sid, access_key)
        return {"sessionId": sid, "tier": tier, "limits": attrs["limits"]}
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid access key")

# class LimitsOut(BaseModel):
#     sessionId: str
#     tier: str
#     limits: dict

# @router.get("/session/limits", response_model=LimitsOut)
# async def limits(sessionId: str):
#     print("Request details - sessionID:", sessionId)
#     s = SessionStore.get_session(sessionId)
#     if not s: raise HTTPException(status_code=404, detail="unknown session")
#     return {"sessionId": s["sessionId"], "tier": s["tier"], "limits": s["limits"]}

# @router.get("/session/limits")
# async def session_limits(
#     request: Request,
#     sessionId: Optional[str] = None,  # query param is optional now
#     x_session_id: Optional[str] = Header(default=None, convert_underscores=False),  # reads "X-Session-Id"
# ):
#     # Prefer header, then explicit query param
#     sid = x_session_id or request.headers.get("X-Session-Id") or sessionId
#     if not sid:
#         raise HTTPException(status_code=401, detail="missing sessionId (header or query)")

#     s = SessionStore.get_session(sid)
#     if not s:
#         raise HTTPException(status_code=404, detail="unknown session; call /session/start")

#     return {"sessionId": sid, "tier": s["tier"], "limits": s["limits"]}

@router.get("/session/limits")
async def session_limits(
    request: Request,
    sessionId: Optional[str] = None,
    x_session_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    sid = x_session_id or request.headers.get("X-Session-Id") or sessionId
    if not sid:
        raise HTTPException(status_code=401, detail="missing sessionId (header or query)")

    prof = SessionStore.get_session(sid)
    if not prof:
        raise HTTPException(status_code=404, detail="unknown session; call /session/start")

    live = SessionStore.get_live_usage(sid)
    # Shape to what the frontend expects
    return {
        "sessionId": sid,
        "tier": live["tier"],
        "limits": {
            "requests": {"used": live["requests"]["used"], "max": live["requests"]["max"]},
            "tools":    {"used": live["tools"]["used"],    "max": live["tools"]["max"]},
            "tokens":   {"used": live["tokens"]["used"],   "max": live["tokens"]["max"]},
        },
    }
