import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "users.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT DEFAULT '{}',
            last_interaction TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            ref_id TEXT PRIMARY KEY,
            user_id TEXT,
            caller_name TEXT,
            reason TEXT,
            summary TEXT,
            already_checked TEXT,
            urgency TEXT,
            language TEXT,
            follow_up TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT
        )
    """)
    conn.commit()
    return conn


def get_user(user_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return None
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "language_preference": row["language_preference"],
        "facts": json.loads(row["facts"] or "{}"),
        "last_interaction": row["last_interaction"],
    }


def upsert_user(user_id: str, name: str, language_preference: str, facts: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO users (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                facts = excluded.facts,
                last_interaction = excluded.last_interaction
        """, (user_id, name, language_preference, json.dumps(facts), now))
        conn.commit()


def create_escalation(
    user_id: str,
    caller_name: str,
    reason: str,
    summary: str,
    already_checked: str,
    urgency: str,
    language: str,
    follow_up: str,
) -> str:
    ref_id = "ESC-" + uuid.uuid4().hex[:6].upper()
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO escalations
            (ref_id, user_id, caller_name, reason, summary, already_checked, urgency, language, follow_up, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
        """, (ref_id, user_id, caller_name, reason, summary, already_checked, urgency, language, follow_up, now))
        conn.commit()
    return ref_id


def get_all_escalations() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM escalations ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]
