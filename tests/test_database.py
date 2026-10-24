import pytest
import requests

import core.database as database
from core.database import (
    DatabaseConnectionError,
    request_supabase,
    supabase_table_url,
    valid_likert,
    validate_ratings,
)


def test_valid_likert_values():
    assert valid_likert(1)
    assert valid_likert(7)


def test_invalid_likert_values():
    assert not valid_likert(0)
    assert not valid_likert(8)
    assert not valid_likert(4.0)


def test_validate_ratings_rejects_invalid_value():
    with pytest.raises(ValueError):
        validate_ratings([1, 4, 8])


def test_supabase_table_url(monkeypatch):
    secrets = {
        "SUPABASE_URL": "https://example.supabase.co/",
        "SUPABASE_SECRET_KEY": "test-key",
    }
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: secrets.get(name, default))

    assert supabase_table_url("daily_checkins") == (
        "https://example.supabase.co/rest/v1/daily_checkins"
    )


def test_supabase_url_rejects_rest_path(monkeypatch):
    secrets = {
        "SUPABASE_URL": "https://example.supabase.co/rest/v1",
        "SUPABASE_SECRET_KEY": "test-key",
    }
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: secrets.get(name, default))

    with pytest.raises(DatabaseConnectionError):
        supabase_table_url("daily_checkins")


def test_connection_error_has_safe_message(monkeypatch):
    secrets = {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SECRET_KEY": "test-key",
    }
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: secrets.get(name, default))

    def fail_request(*args, **kwargs):
        raise requests.exceptions.ConnectionError("private low-level error")

    monkeypatch.setattr(database.requests, "request", fail_request)

    with pytest.raises(DatabaseConnectionError, match="database could not be reached"):
        request_supabase("GET", "daily_checkins")


def test_boolean_is_not_a_rating():
    assert not valid_likert(True)
    assert not valid_likert(False)


def test_sqlite_records_are_scoped_and_evaluation_retry_is_safe(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "ratings.db")
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: default)
    database.init_db()
    first = "KP-ABCDEFGHIJ"
    second = "KP-0123456789"
    database.save_daily_checkin(first, 4, 5, 6)
    database.save_daily_checkin(second, 1, 2, 3)
    assert len(database.load_daily_checkins(first)) == 1
    assert database.load_daily_checkins(first).iloc[0]["mood"] == 4
    values = ("7e67cbe3-e99a-4509-b33b-d367e963ee60", first, 4, 5, 6, 5, 4, 6, 5, 5, 5)
    database.save_evaluation_session(*values)
    database.save_evaluation_session(*values)
    assert len(database.load_evaluation_sessions(first)) == 1
    assert database.load_evaluation_sessions(second).empty
    for invalid in [None, "", "KP-a", "KP-ABCDEFGHIJ&select=*"]:
        with pytest.raises(ValueError):
            database.load_daily_checkins(invalid)


def test_supabase_filters_code_and_ignores_evaluation_retry(monkeypatch):
    calls = []
    monkeypatch.setattr(database, "supabase_available", lambda: True)
    def request(method, table, **kwargs):
        calls.append((method, table, kwargs))
        class Response:
            def json(self):
                return [{"mood_before": 4}] if table == "evaluation_sessions" else []
        return Response()
    monkeypatch.setattr(database, "request_supabase", request)
    database.load_daily_checkins("KP-ABCDEFGHIJ")
    assert calls[0][2]["params"]["anonymous_id"] == "eq.KP-ABCDEFGHIJ"
    assert calls[0][2]["params"]["order"] == "created_at.desc,id.desc"
    database.save_evaluation_session("7e67cbe3-e99a-4509-b33b-d367e963ee60", "KP-ABCDEFGHIJ", *([4] * 9))
    assert calls[1][2]["params"] == {"on_conflict": "interaction_id"}
    assert "ignore-duplicates" in calls[1][2]["headers"]["Prefer"]


def test_incomplete_database_setup_fails_closed(monkeypatch):
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: "https://example.supabase.co" if name == "SUPABASE_URL" else default)
    with pytest.raises(DatabaseConnectionError, match="incomplete"):
        database.init_db()


def test_modern_secret_key_is_not_sent_as_jwt(monkeypatch):
    monkeypatch.setattr(database, "supabase_key", lambda: "sb_secret_test")
    headers = database.supabase_headers()
    assert headers["apikey"] == "sb_secret_test"
    assert "Authorization" not in headers


def test_retry_returns_original_saved_ratings(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "ratings.db")
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: default)
    database.init_db()
    identity = ("7e67cbe3-e99a-4509-b33b-d367e963ee60", "KP-ABCDEFGHIJ")
    first = database.save_evaluation_session(*identity, *([4] * 9))
    second = database.save_evaluation_session(*identity, *([6] * 9))
    assert first == second
    assert second["mood_after"] == 4
