"""Server-side AI request quotas. IPs are HMAC'd; raw addresses are never stored.

These counters reduce accidental/automated provider spend, but Streamlit's client IP
is spoofable. Provider spend caps and host-level rate limiting are still recommended.
"""
import hashlib
import hmac
import ipaddress
import sqlite3
import time
from contextlib import closing

from core import database
from core.config import get_secret


class QuotaUnavailable(Exception):
    """AI must fall back rather than send an unmetered provider request."""


# Session caps prevent one person consuming a large shared-IP allowance.
# The broad IP caps are higher to accommodate shared student / household networks.
# A global daily cap bounds spend even if a client can change or spoof their IP.
RULES = (
    ("session", 600, 10),
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
        # Combine IPv6 privacy addresses inside the same /64 prefix.
        return str(ipaddress.ip_network(f"{ip}/64", strict=False))
    return str(ip)


def _local_reserve(ip_key, session_key):
    """SQLite quotas are atomic across sessions in a single local deployment."""
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


def consume_ai_quota(client_ip, session_id):
    """Reserve one AI call before making it. Never fail open on missing quota storage."""
    secret = get_secret("RATE_LIMIT_SECRET")
    if not isinstance(secret, str) or len(secret) < 32 or not isinstance(session_id, str) or not session_id:
        raise QuotaUnavailable("AI usage checks are not configured.")
    ip_scope = _ip_scope(client_ip)
    # Unknown IPs must not force unrelated users into one shared network bucket.
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
