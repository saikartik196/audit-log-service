import hashlib
import json
import sqlite3
from datetime import datetime, timezone

from app.database import get_connection
from app.schemas import AuditEventCreate


def create_audit_event(event: AuditEventCreate):
    timestamp = (
        event.timestamp.astimezone(timezone.utc).isoformat()
        if event.timestamp
        else datetime.now(timezone.utc).isoformat()
    )

    payload_json = json.dumps(
        event.payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        previous_event = connection.execute(
            """
            SELECT content_hash
            FROM audit_events
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        previous_hash = (
            previous_event["content_hash"]
            if previous_event
            else "GENESIS"
        )

        event_data = {
            "event_type": event.eventType,
            "actor_id": event.actorId,
            "resource_type": event.resourceType,
            "resource_id": event.resourceId,
            "payload": event.payload,
            "timestamp": timestamp,
            "previous_hash": previous_hash,
        }

        canonical_json = json.dumps(
            event_data,
            sort_keys=True,
            separators=(",", ":"),
        )

        content_hash = hashlib.sha256(
            canonical_json.encode("utf-8")
        ).hexdigest()

        cursor = connection.execute(
            """
            INSERT INTO audit_events (
                event_type,
                actor_id,
                resource_type,
                resource_id,
                payload,
                timestamp,
                content_hash,
                previous_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.eventType,
                event.actorId,
                event.resourceType,
                event.resourceId,
                payload_json,
                timestamp,
                content_hash,
                previous_hash,
            ),
        )

        connection.commit()

        return {
            "id": cursor.lastrowid,
            "timestamp": timestamp,
            "contentHash": content_hash,
            "previousHash": previous_hash,
        }
