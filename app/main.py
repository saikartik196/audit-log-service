from fastapi import HTTPException
from app.export_service import export_audit_events
from contextlib import asynccontextmanager

from fastapi import FastAPI, status

from app.audit_service import create_audit_event
from app.database import initialize_database
from app.schemas import AuditEventCreate
from app.verification import verify_audit_chain

from datetime import datetime, timezone

from fastapi import Query
from app.query_service import query_audit_events


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    from app.redaction_service import initialize_redaction_table
    initialize_redaction_table()
    yield


app = FastAPI(
    title="Audit Log Service",
    version="0.2.0",
    description="A service for recording and verifying audit events.",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/audit", status_code=status.HTTP_201_CREATED)
def write_audit_event(event: AuditEventCreate):
    return create_audit_event(event)

@app.get("/audit/verify")
def verify_audit_events():
    return verify_audit_chain()


@app.get("/audit")
def get_audit_events(
    actorId: str | None = None,
    eventType: str | None = None,
    resourceType: str | None = None,
    resourceId: str | None = None,
    startTime: datetime | None = None,
    endTime: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    def to_utc(value):
        if value is None:
            return None

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc).isoformat()

    return query_audit_events(
        actor_id=actorId,
        event_type=eventType,
        resource_type=resourceType,
        resource_id=resourceId,
        start_time=to_utc(startTime),
        end_time=to_utc(endTime),
        limit=limit,
        offset=offset,
    )


@app.get("/audit/export")
def export_audit_records(
    actorId: str | None = None,
    resourceId: str | None = None,
):
    if actorId is None and resourceId is None:
        raise HTTPException(
            status_code=422,
            detail="Provide actorId or resourceId",
        )

    return export_audit_events(
        actor_id=actorId,
        resource_id=resourceId,
    )


@app.post("/audit/archive")
def archive_audit_records():
    from app.retention_service import archive_expired_events
    return archive_expired_events()


from pydantic import BaseModel, Field
from app.redaction_service import redact_event_field


class RedactionRequest(BaseModel):
    fieldPath: str = Field(min_length=1)


@app.post("/audit/{event_id}/redact")
def redact_audit_record(event_id: int, request: RedactionRequest):
    try:
        return redact_event_field(event_id, request.fieldPath)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


# Scenario C: Audit access to client account data.
# Records access outcomes supplied by a trusted calling system.
class AccountAccessRequest(BaseModel):
    actorId: str = Field(min_length=1)
    accountId: str = Field(min_length=1)
    action: str = Field(min_length=1)
    outcome: str
    justification: str | None = None


@app.post("/audit/account-access", status_code=status.HTTP_201_CREATED)
def record_account_access(request: AccountAccessRequest):
    if request.outcome not in {"ALLOWED", "DENIED"}:
        raise HTTPException(
            status_code=422,
            detail="outcome must be ALLOWED or DENIED",
        )

    event = AuditEventCreate(
        eventType="CLIENT_ACCOUNT_ACCESS",
        actorId=request.actorId,
        resourceType="CLIENT_ACCOUNT",
        resourceId=request.accountId,
        payload={
            "action": request.action,
            "outcome": request.outcome,
            "justification": request.justification,
        },
    )

    return create_audit_event(event)
