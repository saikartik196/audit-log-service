from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eventType: str = Field(min_length=1)
    actorId: str = Field(min_length=1)
    resourceType: str = Field(min_length=1)
    resourceId: str = Field(min_length=1)
    payload: dict[str, Any]
    timestamp: datetime | None = None
