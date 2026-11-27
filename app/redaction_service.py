import copy
import json
import sqlite3
from datetime import datetime, timezone

from app.database import get_connection


def initialize_redaction_table():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_redactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                field_path TEXT NOT NULL,
                redacted_at TEXT NOT NULL,
                UNIQUE(event_id, field_path),
                FOREIGN KEY(event_id) REFERENCES audit_events(id)
            )
        """)
        connection.commit()


def redact_event_field(event_id: int, field_path: str):
    if not field_path or not field_path.strip():
        raise ValueError("fieldPath cannot be empty")

    parts = field_path.split(".")

    if any(not part for part in parts):
        raise ValueError("Invalid fieldPath")

    with get_connection() as connection:
        row = connection.execute(
            "SELECT payload FROM audit_events WHERE id = ?",
            (event_id,),
        ).fetchone()

        if row is None:
            raise LookupError("Audit event not found")

        payload = json.loads(row["payload"])
        current = payload

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                raise ValueError("Field path not found")
            current = current[part]

        connection.execute(
            """
            INSERT OR IGNORE INTO audit_redactions (
                event_id, field_path, redacted_at
            )
            VALUES (?, ?, ?)
            """,
            (
                event_id,
                field_path,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        connection.commit()

    return {
        "eventId": event_id,
        "fieldPath": field_path,
        "redacted": True,
    }


def apply_redactions(event_id: int, payload: dict):
    result = copy.deepcopy(payload)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT field_path
            FROM audit_redactions
            WHERE event_id = ?
            ORDER BY field_path
            """,
            (event_id,),
        ).fetchall()

    for row in rows:
        current = result
        parts = row["field_path"].split(".")

        for part in parts[:-1]:
            if not isinstance(current, dict):
                break
            current = current.get(part)

        if isinstance(current, dict) and parts[-1] in current:
            current[parts[-1]] = "[REDACTED]"

    return result
