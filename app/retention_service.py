import os
from datetime import datetime, timedelta, timezone

from app.database import get_connection


def archive_expired_events():
    retention_days = int(os.getenv("AUDIT_RETENTION_DAYS", "365"))

    if retention_days < 1:
        raise ValueError("AUDIT_RETENTION_DAYS must be at least 1")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE audit_events
            SET archived_at = ?
            WHERE archived_at IS NULL
              AND julianday(timestamp) < julianday(?)
            """,
            (now.isoformat(), cutoff.isoformat()),
        )
        connection.commit()

        return {
            "archivedCount": cursor.rowcount,
            "retentionDays": retention_days,
            "cutoffTimestamp": cutoff.isoformat(),
        }
