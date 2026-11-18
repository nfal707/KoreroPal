import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

import core.database as database
import core.limits as limits
from core.safety import assess_risk


@pytest.fixture
def quota(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "ratings.db")
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: default)
    monkeypatch.setattr(limits, "get_secret", lambda name, default=None: "x" * 40 if name == "RATE_LIMIT_SECRET" else default)
    monkeypatch.setattr(limits.time, "time", lambda: 1816000000)
    database.init_db()
    return lambda ip, session: limits.consume_ai_quota(ip, session)


def test_session_is_limited_in_ten_minute_window(quota):
    assert all(quota("192.0.2.5", "session-one") for _ in range(10))
    assert quota("192.0.2.5", "session-one") is False
    assert quota("192.0.2.5", "session-two") is True


def test_shared_ip_has_broad_but_finite_budget(quota):
    for session in range(6):
        assert all(quota("192.0.2.9", f"s{session}") for _ in range(10))
    assert quota("192.0.2.9", "seventh") is False
    assert quota("192.0.2.10", "different-network") is True


def test_session_daily_limit_even_across_windows(quota, monkeypatch):
    # 35 requests in distinct windows; subsequent request is blocked for this session.
    base = 1816000000
    for window in range(4):
        monkeypatch.setattr(limits.time, "time", lambda window=window: base + window * 600)
        for _ in range(10 if window < 3 else 5):
            assert quota("192.0.2.2", "daily-session")
    assert quota("192.0.2.2", "daily-session") is False


def test_missing_secret_disables_ai(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "ratings.db")
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: default)
    monkeypatch.setattr(limits, "get_secret", lambda name, default=None: None)
    database.init_db()
    with pytest.raises(limits.QuotaUnavailable):
        limits.consume_ai_quota("192.0.2.10", "session")


def test_ipv6_privacy_prefix_and_hash():
    assert limits._ip_scope("2001:db8:abcd:2::10") == limits._ip_scope("2001:db8:abcd:2::99")
    assert limits._ip_scope("not an ip") == "unavailable"
    key = limits._digest("ip", "192.0.2.4", "secret")
    assert "192.0.2.4" not in key
    assert len(key) == 64


@pytest.mark.parametrize("message,expected", [
    ("I wish I were dead", "crisis"),
    ("I don't want to wake up", "crisis"),
    ("I hope I don't wake up", "crisis"),
    ("I am thinking about killing myself", "crisis"),
    ("I want to die", "crisis"),
    ("I'm not suicidal", "normal"),
    ("I want to live", "normal"),
    ("I do not want to die", "normal"),
    ("I am hopeless", "high"),
    ("I am stressed about exams", "normal"),
])
def test_safety_regressions(message, expected):
    assert assess_risk(message) == expected


def test_deletion_is_isolated_and_recoverable_empty_state(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "ratings.db")
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: default)
    database.init_db()
    a, b = "KP-ABCDEFGHIJ", "KP-0123456789"
    database.save_daily_checkin(a, 4, 5, 6)
    database.save_daily_checkin(b, 7, 5, 2)
    database.save_evaluation_session("7e67cbe3-e99a-4509-b33b-d367e963ee60", a, *([4] * 9))
    assert database.delete_ratings(a) == 2
    assert database.delete_ratings(a) == 0
    assert database.load_daily_checkins(a).empty
    assert database.load_evaluation_sessions(a).empty
    assert len(database.load_daily_checkins(b)) == 1


def test_local_retention_prunes_expired_rows(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "ratings.db")
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: default)
    database.init_db()
    code = "KP-ABCDEFGHIJ"
    database.save_daily_checkin(code, 2, 3, 4)
    old = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute("UPDATE daily_checkins SET created_at = ?", (old,))
    database.init_db()
    assert database.load_daily_checkins(code).empty
