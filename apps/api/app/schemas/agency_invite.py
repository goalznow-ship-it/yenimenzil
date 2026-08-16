"""Agency team invite schemas (Phase 14)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AgencyInviteCreate(BaseModel):
    email: EmailStr
    role: str = Field(default="agent", pattern="^(agent|agency_admin)$")


class AgencyInviteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agency_id: uuid.UUID
    email: str
    role: str
    status: str
    token: str
    created_by: uuid.UUID | None
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime


class AgencyImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[dict] = []
