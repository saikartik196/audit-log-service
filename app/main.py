from contextlib import asynccontextmanager

from fastapi import FastAPI, status

from app.audit_service import create_audit_event
from app.database import initialize_database
from app.schemas import AuditEventCreate


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
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
