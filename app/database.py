
import sqlite3
from pathlib import Path

DATABASE_PATH = Path("audit.db")


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                archived_at TEXT
            )
        """)

        # Migrate existing databases without losing audit events.
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(audit_events)"
            ).fetchall()
        }

        if "archived_at" not in columns:
            connection.execute(
                "ALTER TABLE audit_events ADD COLUMN archived_at TEXT"
            )

        connection.commit()

