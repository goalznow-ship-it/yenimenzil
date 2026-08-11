from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReportReason, ReportStatus


class ReportBase(BaseModel):
    reason: ReportReason
    description: str | None = Field(None, max_length=2000)
    status: ReportStatus = ReportStatus.OPEN


class ReportCreate(ReportBase):
    property_id: uuid.UUID
    reporter_id: uuid.UUID | None = None


class ReportUpdate(BaseModel):
    status: ReportStatus | None = None
    resolution_note: str | None = Field(None, max_length=2000)
    reviewer_id: uuid.UUID | None = None


class ReportRead(ReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    reporter_id: uuid.UUID | None = None
    reviewer_id: uuid.UUID | None = None
    created_at: datetime
    reviewed_at: datetime | None = None
    resolution_note: str | None = None
