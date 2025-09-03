# agent_multi/runtime/session_store.py
from __future__ import annotations
from dataclasses import field
import time, uuid, hashlib, json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple
from boto3.dynamodb.conditions import Attr
from .dynamo import _ddb_table as table
from .config import DDB_TTL_DAYS, ANON_LIMITS, ELEV_LIMITS, ADMIN_LIMITS, ACCESS_KEY_ELEVATED, ACCESS_KEY_ADMIN
from decimal import Decimal



# Keys
def _pk_session(session_id: str) -> str: return f"SESSION#{session_id}"
def _sk_profile() -> str:                return "PROFILE"
def _sk_win(metric: str, bucket: str) -> str: return f"WIN#{metric}#{bucket}"

def _now() -> datetime: return datetime.now(tz=timezone.utc)
def _minute_bucket(ts: datetime) -> str: return ts.strftime("%Y%m%d%H%M")
def _day_bucket(ts: datetime) -> str:    return ts.strftime("%Y%m%d")
def _D(n) -> Decimal:
    return Decimal(int(n))

def _limits_for_tier(tier: str) -> Dict[str, Any]:
    if tier == "admin":    return ADMIN_LIMITS
    if tier == "elevated": return ELEV_LIMITS
    return ANON_LIMITS

def _ttl_epoch(days: int) -> int:
    return int((_now() + timedelta(days=days)).timestamp())

def ip_hash(remote_ip: str) -> str:
    return hashlib.sha256((remote_ip or "").encode("utf-8")).hexdigest()[:16]

def _coerce_int(v) -> int:
    if v is None:
        return 0
    if isinstance(v, (int,)):
        return v
    if isinstance(v, Decimal):
        return int(v)
    # strings etc.
    try:
        return int(v)
    except Exception:
        return 0

def _is_unlimited(v) -> bool:
    # support None or negative sentinel (e.g., -1) as "unlimited"
    try:
        if v is None:
            return True
        return int(v) < 0
    except Exception:
        return False

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
    def _read_window_counter(session_id: str, metric: str, ts: datetime) -> int:
        """Reads the current counter for the active bucket of a metric."""
        if metric in ("requests", "tools"):
            bucket = _minute_bucket(ts)
        else:
            bucket = _day_bucket(ts)
        pk = _pk_session(session_id)
        sk = _sk_win(metric, bucket)
        try:
            res = table().get_item(Key={"PK": pk, "SK": sk})
            attrs = res.get("Item") or {}
            return _coerce_int(attrs.get("counter"))
        except Exception:
            return 0
        
    @staticmethod
    def get_live_usage(session_id: str) -> Dict[str, Any]:
        """
        Returns live usage for the active windows:
        - requests: current minute
        - tools:    current minute
        - tokens:   current day
        """
        prof = SessionStore.get_session(session_id)
        if not prof:
            raise ValueError("unknown_session")
        limits = prof.get("limits") or {}

        now = _now()

        req_used   = SessionStore._read_window_counter(session_id, "requests", now)
        tools_used = SessionStore._read_window_counter(session_id, "tools", now)
        tok_used   = SessionStore._read_window_counter(session_id, "tokens", now)

        # remaining time in the active windows
        req_remain_sec = max(0, 60 - now.second)
        tools_remain_sec = req_remain_sec
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        tok_remain_sec = max(0, int((midnight - now).total_seconds()))

        def norm_max(key: str):
            return None if limits.get(key) is None else _coerce_int(limits.get(key))

        return {
            "requests": {
                "used": req_used,
                "max": norm_max("requests_per_min"),
                "resetInSec": req_remain_sec,
            },
            "tools": {
                "used": tools_used,
                "max": norm_max("tools_per_min"),
                "resetInSec": tools_remain_sec,
            },
            "tokens": {
                "used": tok_used,
                "max": norm_max("tokens_per_day"),
                "resetInSec": tok_remain_sec,
            },
            "tier": prof.get("tier", "anonymous"),
        }


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
            "SET #f = if_not_exists(#f, :zero) + :inc, "
            "    expiresAt = :ttl"
        )
        vals = {":inc": _D(int(inc)), ":zero": _D(0), ":ttl": _D(ttl)}
        res = table().update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression=expr,
            ExpressionAttributeNames={"#f": "counter"},
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
