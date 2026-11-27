from datetime import datetime, timezone

from app.query_service import query_audit_events
from app.verification import verify_audit_chain
from app.signing_service import sign_bundle


def export_audit_events(
    actor_id=None,
    resource_id=None,
):
    if actor_id is None and resource_id is None:
        raise ValueError(
            "At least one of actorId or resourceId is required"
        )

    # Verify the complete database chain, not just the selected events.
    verification = verify_audit_chain()

    if not verification["valid"]:
        return {
            "exported": False,
            "reason": "Audit chain verification failed",
            "verification": verification,
        }

    # Retrieve matching events in batches.
    events = []
    offset = 0
    batch_size = 100

    while True:
        result = query_audit_events(
            actor_id=actor_id,
            resource_id=resource_id,
            limit=batch_size,
            offset=offset,
        )

        events.extend(result["events"])

        if len(events) >= result["total"]:
            break

        offset += batch_size

    bundle = {
        "exported": True,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "filters": {
            "actorId": actor_id,
            "resourceId": resource_id,
        },
        "total": len(events),
        "verification": verification,
        "events": events,
    }


    signed = sign_bundle(bundle)

    return {
        **bundle,
        "signedBundle": signed,
    }
