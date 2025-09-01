# agent_multi/runtime/session_store.py
from __future__ import annotations
import time, uuid, hashlib, json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple
from boto3.dynamodb.conditions import Attr
from .dynamo import table
from .config import DDB_TTL_DAYS, ANON_LIMITS, ELEV_LIMITS, ADMIN_LIMITS, ACCESS_KEY_ELEVATED, ACCESS_KEY_ADMIN


# Keys
def _pk_session(session_id: str) -> str: return f"SESSION#{session_id}"
def _sk_profile() -> str:                return "PROFILE"
def _sk_win(metric: str, bucket: str) -> str: return f"WIN#{metric}#{bucket}"

def _now() -> datetime: return datetime.now(tz=timezone.utc)
def _minute_bucket(ts: datetime) -> str: return ts.strftime("%Y%m%d%H%M")
def _day_bucket(ts: datetime) -> str:    return ts.strftime("%Y%m%d")

def _limits_for_tier(tier: str) -> Dict[str, Any]:
    if tier == "admin":    return ADMIN_LIMITS
    if tier == "elevated": return ELEV_LIMITS
    return ANON_LIMITS

def _ttl_epoch(days: int) -> int:
    return int((_now() + timedelta(days=days)).timestamp())

def ip_hash(remote_ip: str) -> str:
    return hashlib.sha256((remote_ip or "").encode("utf-8")).hexdigest()[:16]

class SessionStore:
    @staticmethod
    def start_session(remote_ip: str, user_agent: str) -> Dict[str, Any]:
        sid = str(uuid.uuid4())
        pk, sk = _pk_session(sid), _sk_profile()
        lim = _limits_for_tier("anonymous")
        item = {
            "PK": pk,
            "SK": sk,
            "entity": "SESSION",
            "sessionId": sid,
            "tier": "anonymous",
            "limits": lim,
            "createdAt": _now().isoformat(),
            "lastSeenAt": _now().isoformat(),
            "ipHash": ip_hash(remote_ip),
            "userAgent": user_agent[:200],
            "flags": {"allowlist": False},
            "expiresAt": _ttl_epoch(DDB_TTL_DAYS),  # TTL attr
        }
        table().put_item(Item=item, ConditionExpression=Attr("PK").not_exists())
        return item

    @staticmethod
    def get_session(session_id: str) -> Dict[str, Any] | None:
        res = table().get_item(Key={"PK": _pk_session(session_id), "SK": _sk_profile()})
        return res.get("Item")

    @staticmethod
    def touch(session_id: str):
        table().update_item(
            Key={"PK": _pk_session(session_id), "SK": _sk_profile()},
            UpdateExpression="SET lastSeenAt=:t",
            ExpressionAttributeValues={":t": _now().isoformat()},
        )

    @staticmethod
    def upgrade(session_id: str, access_key: str) -> Tuple[Dict[str, Any], str]:
        tier = None
        if access_key and ACCESS_KEY_ADMIN and access_key == ACCESS_KEY_ADMIN:
            tier = "admin"
        elif access_key and ACCESS_KEY_ELEVATED and access_key == ACCESS_KEY_ELEVATED:
            tier = "elevated"
        else:
            raise ValueError("invalid_access_key")

        limits = _limits_for_tier(tier)
        res = table().update_item(
            Key={"PK": _pk_session(session_id), "SK": _sk_profile()},
            UpdateExpression="SET tier=:tier, limits=:limits",
            ExpressionAttributeValues={":tier": tier, ":limits": limits},
            ReturnValues="ALL_NEW",
        )
        return res["Attributes"], tier

    # ----------- Rate limiting (atomic counters per window) -----------

    @staticmethod
    def _bump_window_counter(session_id: str, metric: str, inc: int, max_allowed, ttl_secs: int) -> Tuple[bool, int]:
        """
        Bumps WIN item: PK=SESSION#id, SK=WIN#metric#bucket; returns (allowed, remaining_secs_in_window)
        """
        now = _now()
        bucket = _minute_bucket(now) if metric in ("requests", "tools") else _day_bucket(now)
        sk = _sk_win(metric, bucket)
        pk = _pk_session(session_id)

        # Remaining seconds in window
        if metric in ("requests", "tools"):
            # until next minute boundary
            remain = 60 - (now.second)
        else:
            # until next day boundary
            midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            remain = int((midnight - now).total_seconds())

        # Admin/allowlist bypass
        prof = SessionStore.get_session(session_id)
        if not prof:
            raise ValueError("unknown_session")
        if prof["tier"] == "admin" or (prof.get("flags") or {}).get("allowlist"):
            return True, remain
        if max_allowed == float("inf"):
            return True, remain

        # Atomic update with if_not_exists
        # Keep a small TTL on windows (e.g., +2 minutes or +2 days)
        ttl = int(time.time()) + (120 if metric in ("requests", "tools") else 2*24*3600)
        expr = (
            "SET counter = if_not_exists(counter, :zero) + :inc, "
            "    expiresAt = :ttl"
        )
        vals = {":inc": inc, ":zero": 0, ":ttl": ttl}
        res = table().update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression=expr,
            ExpressionAttributeValues=vals,
            ReturnValues="ALL_NEW",
        )
        current = int(res["Attributes"].get("counter", 0))
        allowed = current <= (max_allowed or 0)
        return allowed, remain

    @staticmethod
    def enforce_request(session_id: str) -> Tuple[bool, Dict[str, Any]]:
        prof = SessionStore.get_session(session_id)
        if not prof:
            return False, {"code": "unknown_session"}
        allowed, sec = SessionStore._bump_window_counter(
            session_id, "requests", 1, prof["limits"]["requests_per_min"], 120
        )
        if not allowed:
            return False, {"code": "rate_limited", "where": "session", "metric": "requests", "retryAfterSec": sec}
        return True, {}

    @staticmethod
    def enforce_tools(session_id: str, count: int) -> Tuple[bool, Dict[str, Any]]:
        if count <= 0: return True, {}
        prof = SessionStore.get_session(session_id)
        if not prof:
            return False, {"code": "unknown_session"}
        allowed, sec = SessionStore._bump_window_counter(
            session_id, "tools", count, prof["limits"]["tools_per_min"], 120
        )
        if not allowed:
            return False, {"code": "rate_limited", "where": "session", "metric": "tools", "retryAfterSec": sec}
        return True, {}

    @staticmethod
    def enforce_tokens(session_id: str, tokens: int) -> Tuple[bool, Dict[str, Any]]:
        if tokens <= 0: return True, {}
        prof = SessionStore.get_session(session_id)
        if not prof:
            return False, {"code": "unknown_session"}
        allowed, sec = SessionStore._bump_window_counter(
            session_id, "tokens", tokens, prof["limits"]["tokens_per_day"], 2*24*3600
        )
        if not allowed:
            return False, {"code": "rate_limited", "where": "session", "metric": "tokens", "retryAfterSec": sec}
        return True, {}
