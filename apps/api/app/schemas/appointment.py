from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ViewingAppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    requester_id: uuid.UUID
    owner_id: uuid.UUID
    scheduled_at: datetime
    status: str
    note: str | None = None
    created_at: datetime
    property_title: str | None = None
    property_cover: str | None = None
    requester_name: str | None = None
    owner_name: str | None = None


class ViewingAppointmentCreate(BaseModel):
    scheduled_at: datetime
    note: str | None = Field(None, max_length=1000)


class ViewingAppointmentUpdate(BaseModel):
    scheduled_at: datetime | None = None
    status: str | None = Field(
        None, pattern=r"^(pending|confirmed|declined|cancelled|rescheduled|completed)$"
    )
    note: str | None = Field(None, max_length=1000)
