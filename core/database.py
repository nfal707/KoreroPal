import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

from core.config import get_secret
from core.identity import validate_anonymous_id


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "koreropal.db"
SUPABASE_TIMEOUT = 15


class DatabaseConnectionError(Exception):
    pass


def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def supabase_key():
    key = get_secret("SUPABASE_SECRET_KEY")

    if key:
        return str(key).strip()

    key = get_secret("SUPABASE_SERVICE_ROLE_KEY")

    if key:
        return str(key).strip()

    return None


def supabase_url():
    value = get_secret("SUPABASE_URL")

    if not value:
        return None

    return str(value).strip().rstrip("/")


def supabase_available():
    url = supabase_url()
    key = supabase_key()
    if bool(url) != bool(key):
        raise DatabaseConnectionError("Database setup is incomplete. Please ask the app owner to check its configuration.")
    return bool(url and key)


def database_name():
    if supabase_available():
        return "Supabase"

    return "local SQLite"


def supabase_headers():
    key = supabase_key()

    if not key:
        raise DatabaseConnectionError("The Supabase secret key is missing.")

    headers = {
        "apikey": key,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {key}"
    return headers


def supabase_table_url(table_name):
    base_url = supabase_url()

    if not base_url:
        raise DatabaseConnectionError("The Supabase project URL is missing.")

    parsed_url = urlparse(base_url)

    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise DatabaseConnectionError(
            "SUPABASE_URL must be the HTTPS project URL from the Supabase dashboard."
        )

    if parsed_url.username or parsed_url.password or parsed_url.query or parsed_url.fragment:
        raise DatabaseConnectionError("The database project URL is not valid.")

    if parsed_url.path not in {"", "/"}:
        raise DatabaseConnectionError(
            "SUPABASE_URL must not include /rest/v1. Use only the project URL."
        )

    if table_name not in {"daily_checkins", "evaluation_sessions"}:
        raise ValueError("Unknown ratings table.")

    return f"{base_url}/rest/v1/{table_name}"


def request_supabase(method, table_name, **kwargs):
    try:
        headers = supabase_headers()
        headers.update(kwargs.pop("headers", {}))
        response = requests.request(
            method,
            supabase_table_url(table_name),
            headers=headers,
            allow_redirects=False,
            timeout=SUPABASE_TIMEOUT,
            **kwargs,
        )
        response.raise_for_status()
        if 300 <= response.status_code < 400:
            raise DatabaseConnectionError("The database returned an unexpected redirect.")
        return response
    except requests.exceptions.Timeout as error:
        raise DatabaseConnectionError(
            "The database took too long to respond. Please try again."
        ) from error
    except requests.exceptions.ConnectionError as error:
        raise DatabaseConnectionError(
            "The database could not be reached. Check that the Supabase project is active and that SUPABASE_URL matches the project dashboard."
        ) from error
    except requests.exceptions.HTTPError as error:
        status_code = error.response.status_code if error.response is not None else None

        if status_code in {401, 403}:
            message = "Supabase rejected the database key. Replace it in the app secrets."
        elif status_code == 404:
            message = "The Supabase table could not be found. Run supabase_schema.sql."
        else:
            message = "Supabase returned an error while handling the request."

        raise DatabaseConnectionError(message) from error
    except requests.exceptions.RequestException as error:
        raise DatabaseConnectionError(
            "The database request could not be completed. Please try again."
        ) from error


def init_db():
    if supabase_available():
        return

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anonymous_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            mood INTEGER NOT NULL,
            stress INTEGER NOT NULL,
            energy INTEGER NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluation_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interaction_id TEXT NOT NULL UNIQUE,
            anonymous_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            mood_before INTEGER NOT NULL,
            stress_before INTEGER NOT NULL,
            energy_before INTEGER NOT NULL,
            mood_after INTEGER NOT NULL,
            stress_after INTEGER NOT NULL,
            energy_after INTEGER NOT NULL,
            felt_heard INTEGER NOT NULL,
            response_relevance INTEGER NOT NULL,
            would_use_again INTEGER NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def valid_likert(value):
    return type(value) is int and 1 <= value <= 7


def validate_ratings(values):
    for value in values:
        if not valid_likert(value):
            raise ValueError("All Likert ratings must be whole numbers from 1 to 7.")


def save_daily_checkin(anonymous_id, mood, stress, energy):
    validate_anonymous_id(anonymous_id)
    validate_ratings([mood, stress, energy])

    row = {
        "anonymous_id": anonymous_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mood": mood,
        "stress": stress,
        "energy": energy,
    }

    if supabase_available():
        request_supabase("POST", "daily_checkins", json=row)
        return

    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO daily_checkins (anonymous_id, created_at, mood, stress, energy)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            row["anonymous_id"],
            row["created_at"],
            row["mood"],
            row["stress"],
            row["energy"],
        ),
    )
    conn.commit()
    conn.close()


def save_evaluation_session(
    interaction_id,
    anonymous_id,
    mood_before,
    stress_before,
    energy_before,
    mood_after,
    stress_after,
    energy_after,
    felt_heard,
    response_relevance,
    would_use_again,
):
    validate_anonymous_id(anonymous_id)
    validate_ratings(
        [
            mood_before,
            stress_before,
            energy_before,
            mood_after,
            stress_after,
            energy_after,
            felt_heard,
            response_relevance,
            would_use_again,
        ]
    )

    row = {
        "interaction_id": interaction_id,
        "anonymous_id": anonymous_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mood_before": mood_before,
        "stress_before": stress_before,
        "energy_before": energy_before,
        "mood_after": mood_after,
        "stress_after": stress_after,
        "energy_after": energy_after,
        "felt_heard": felt_heard,
        "response_relevance": response_relevance,
        "would_use_again": would_use_again,
    }

    if supabase_available():
        request_supabase(
            "POST", "evaluation_sessions", json=row,
            params={"on_conflict": "interaction_id"},
            headers={"Prefer": "resolution=ignore-duplicates,return=minimal"},
        )
        response = request_supabase(
            "GET", "evaluation_sessions",
            params={"select": "*", "interaction_id": f"eq.{interaction_id}", "anonymous_id": f"eq.{anonymous_id}", "limit": "1"},
        )
        saved = response.json()
        if not saved:
            raise DatabaseConnectionError("The saved reflection could not be confirmed. Please try saving again.")
        return saved[0]

    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO evaluation_sessions (
            interaction_id,
            anonymous_id,
            created_at,
            mood_before,
            stress_before,
            energy_before,
            mood_after,
            stress_after,
            energy_after,
            felt_heard,
            response_relevance,
            would_use_again
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(interaction_id) DO NOTHING
        """,
        (
            row["interaction_id"],
            row["anonymous_id"],
            row["created_at"],
            row["mood_before"],
            row["stress_before"],
            row["energy_before"],
            row["mood_after"],
            row["stress_after"],
            row["energy_after"],
            row["felt_heard"],
            row["response_relevance"],
            row["would_use_again"],
        ),
    )
    conn.commit()
    conn.row_factory = sqlite3.Row
    saved = conn.execute(
        "SELECT * FROM evaluation_sessions WHERE interaction_id = ? AND anonymous_id = ?",
        (interaction_id, anonymous_id),
    ).fetchone()
    conn.close()
    if saved is None:
        raise DatabaseConnectionError("The saved reflection could not be confirmed.")
    return dict(saved)


def load_supabase_table(table_name, anonymous_id):
    validate_anonymous_id(anonymous_id)
    params = {
        "select": "*",
        "order": "created_at.desc,id.desc",
        "limit": "5000",
        "anonymous_id": f"eq.{anonymous_id}",
    }
    response = request_supabase("GET", table_name, params=params)
    return pd.DataFrame(response.json()).iloc[::-1].reset_index(drop=True)


def load_daily_checkins(anonymous_id):
    validate_anonymous_id(anonymous_id)
    if supabase_available():
        return load_supabase_table("daily_checkins", anonymous_id)

    with closing(connect()) as conn:
        return pd.read_sql_query(
            "SELECT * FROM daily_checkins WHERE anonymous_id = ? ORDER BY created_at ASC, id ASC",
            conn, params=(anonymous_id,),
        )


def load_evaluation_sessions(anonymous_id):
    validate_anonymous_id(anonymous_id)
    if supabase_available():
        return load_supabase_table("evaluation_sessions", anonymous_id)

    with closing(connect()) as conn:
        return pd.read_sql_query(
            "SELECT * FROM evaluation_sessions WHERE anonymous_id = ? ORDER BY created_at ASC, id ASC",
            conn, params=(anonymous_id,),
        )
