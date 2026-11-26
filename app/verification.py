import hashlib
import json

from app.database import get_connection


def calculate_event_hash(row):
    event_data = {
        "event_type": row["event_type"],
        "actor_id": row["actor_id"],
        "resource_type": row["resource_type"],
        "resource_id": row["resource_id"],
        "payload": json.loads(row["payload"]),
        "timestamp": row["timestamp"],
        "previous_hash": row["previous_hash"],
    }

    canonical_json = json.dumps(
        event_data,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def verify_audit_chain():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM audit_events ORDER BY id ASC"
        ).fetchall()

    expected_previous_hash = "GENESIS"

    for row in rows:
        event_id = row["id"]

        if row["previous_hash"] != expected_previous_hash:
            return {
                "valid": False,
                "checkedEvents": event_id,
                "failedEventId": event_id,
                "reason": "Previous hash mismatch",
            }

        try:
            calculated_hash = calculate_event_hash(row)
        except (ValueError, TypeError, KeyError):
            return {
                "valid": False,
                "checkedEvents": event_id,
                "failedEventId": event_id,
                "reason": "Invalid stored event data",
            }

        if row["content_hash"] != calculated_hash:
            return {
                "valid": False,
                "checkedEvents": event_id,
                "failedEventId": event_id,
                "reason": "Content hash mismatch",
            }

        expected_previous_hash = row["content_hash"]

    return {
        "valid": True,
        "checkedEvents": len(rows),
        "failedEventId": None,
        "reason": None,
    }
