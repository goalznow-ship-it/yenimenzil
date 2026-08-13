from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AnalyticsEventType


class AnalyticsEventBase(BaseModel):
    event_type: AnalyticsEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = Field(None, max_length=45)
    user_agent: str | None = Field(None, max_length=255)


class AnalyticsEventCreate(AnalyticsEventBase):
    user_id: uuid.UUID | None = None
    property_id: uuid.UUID | None = None


class AnalyticsEventRead(AnalyticsEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None = None
    property_id: uuid.UUID | None = None
    created_at: datetime


class PopularSearchRead(BaseModel):
    query: str
    count: int


class ListingAnalyticsRead(BaseModel):
    property_id: uuid.UUID
    views: int = 0
    favorites: int = 0
    phone_reveals: int = 0
    whatsapp_clicks: int = 0
    messages: int = 0
    viewing_requests: int = 0
