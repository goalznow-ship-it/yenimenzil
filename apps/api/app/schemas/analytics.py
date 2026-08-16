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


class DailyAnalyticsPoint(BaseModel):
    date: str
    views: int = 0
    favorites: int = 0
    phone_reveals: int = 0
    whatsapp_clicks: int = 0
    messages: int = 0


class ConversionRates(BaseModel):
    favorite_rate: float = 0.0
    phone_rate: float = 0.0
    whatsapp_rate: float = 0.0
    message_rate: float = 0.0
    viewing_request_rate: float = 0.0


class ListingAnalyticsRead(BaseModel):
    property_id: uuid.UUID
    views: int = 0
    favorites: int = 0
    phone_reveals: int = 0
    whatsapp_clicks: int = 0
    messages: int = 0
    viewing_requests: int = 0
    days: int = 30
    period_views: int = 0
    trend: list[DailyAnalyticsPoint] = []
    conversion: ConversionRates = ConversionRates()


class AgencyListingPoint(BaseModel):
    property_id: uuid.UUID
    title: str
    views: int
    favorites: int
    phone_reveals: int
    messages: int


class AgencyAnalyticsRead(BaseModel):
    agency_id: uuid.UUID | None = None
    agency_name: str = ""
    days: int = 30
    listings_count: int = 0
    total_views: int = 0
    total_favorites: int = 0
    total_leads: int = 0
    avg_price: float = 0.0
    top_listings: list[AgencyListingPoint] = []
