import json

from app.database import get_connection
from app.redaction_service import apply_redactions


def query_audit_events(
    actor_id=None,
    event_type=None,
    resource_type=None,
    resource_id=None,
    start_time=None,
    end_time=None,
    limit=20,
    offset=0,
):
    conditions = []
    parameters = []

    filters = {
        "actor_id": actor_id,
        "event_type": event_type,
        "resource_type": resource_type,
        "resource_id": resource_id,
    }

    for column, value in filters.items():
        if value is not None:
            conditions.append(f"{column} = ?")
            parameters.append(value)

    if start_time is not None:
        conditions.append("timestamp >= ?")
        parameters.append(start_time)

    if end_time is not None:
        conditions.append("timestamp <= ?")
        parameters.append(end_time)

    where_clause = (
        " WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    with get_connection() as connection:
        total = connection.execute(
            "SELECT COUNT(*) FROM audit_events" + where_clause,
            parameters,
        ).fetchone()[0]

        rows = connection.execute(
            "SELECT * FROM audit_events"
            + where_clause
            + " ORDER BY id ASC LIMIT ? OFFSET ?",
            parameters + [limit, offset],
        ).fetchall()

    events = []

    for row in rows:
        events.append({
            "id": row["id"],
            "eventType": row["event_type"],
            "actorId": row["actor_id"],
            "resourceType": row["resource_type"],
            "resourceId": row["resource_id"],
            "payload": apply_redactions(
                row["id"],
                json.loads(row["payload"]),
            ),
            "timestamp": row["timestamp"],
            "contentHash": row["content_hash"],
            "previousHash": row["previous_hash"],
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "events": events,
    }
