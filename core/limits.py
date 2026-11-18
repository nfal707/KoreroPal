import hashlib
import hmac
import ipaddress
import sqlite3
import time
from contextlib import closing

from core import database
from core.config import get_secret


class QuotaUnavailable(Exception):
    pass


RULES = (
    ("session", 600, 25),
    ("session", 86400, 35),
    ("ip", 600, 60),
    ("ip", 86400, 180),
    ("global", 86400, 300),
)


def _digest(kind, value, secret):
    return hmac.new(secret.encode("utf-8"), f"koreropal:{kind}:{value}".encode("utf-8"), hashlib.sha256).hexdigest()


def _ip_scope(value):
    if not value:
        return "unavailable"
    try:
        ip = ipaddress.ip_address(str(value))
    except ValueError:
        return "unavailable"
    if ip.version == 6:
        return str(ipaddress.ip_network(f"{ip}/64", strict=False))
    return str(ip)


def _local_reserve(ip_key, session_key):
    now = int(time.time())
    keys = {"ip": ip_key, "session": session_key, "global": "global"}
    try:
        with closing(database.connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """CREATE TABLE IF NOT EXISTS ai_request_counters (
                    scope TEXT NOT NULL, window_seconds INTEGER NOT NULL,
                    window_start INTEGER NOT NULL, used INTEGER NOT NULL,
                    PRIMARY KEY(scope, window_seconds, window_start)
                )"""
            )
            buckets = []
            for kind, seconds, max_calls in RULES:
                scope = f"{kind}:{keys[kind]}"
                window_start = now - now % seconds
                count = conn.execute(
                    "SELECT used FROM ai_request_counters WHERE scope=? AND window_seconds=? AND window_start=?",
                    (scope, seconds, window_start),
                ).fetchone()
                if count is not None and count[0] >= max_calls:
                    conn.rollback()
                    return False
                buckets.append((scope, seconds, window_start))
            for scope, seconds, window_start in buckets:
                conn.execute(
                    """INSERT INTO ai_request_counters(scope, window_seconds, window_start, used)
                       VALUES (?, ?, ?, 1)
                       ON CONFLICT(scope, window_seconds, window_start)
                       DO UPDATE SET used=used+1""",
                    (scope, seconds, window_start),
                )
            conn.execute("DELETE FROM ai_request_counters WHERE window_start < ?", (now - 172800,))
            conn.commit()
            return True
    except sqlite3.Error as error:
        raise QuotaUnavailable("AI usage checks are temporarily unavailable.") from error


def quota_secret():
    for name in ("RATE_LIMIT_SECRET", "SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY"):
        value = get_secret(name)
        if isinstance(value, str) and len(value.strip()) >= 32:
            return value.strip()
    return None


def consume_ai_quota(client_ip, session_id):
    secret = quota_secret()
    if not isinstance(secret, str) or len(secret) < 32 or not isinstance(session_id, str) or not session_id:
        raise QuotaUnavailable("AI usage checks are not configured.")
    ip_scope = _ip_scope(client_ip)
    if ip_scope == "unavailable":
        ip_scope = f"unavailable-session:{session_id}"
    ip_key = _digest("ip", ip_scope, secret)
    session_key = _digest("session", session_id, secret)
    try:
        if database.supabase_available():
            response = database.request_supabase_rpc(
                "consume_koreropal_ai_quota",
                {"p_ip_key": ip_key, "p_session_key": session_key},
            )
            result = response.json()
            if type(result) is not bool:
                raise QuotaUnavailable("AI quota response was invalid.")
            return result
        return _local_reserve(ip_key, session_key)
    except database.DatabaseConnectionError as error:
        raise QuotaUnavailable("AI usage checks are temporarily unavailable.") from error
