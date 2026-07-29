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
