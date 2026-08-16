"""Residential complex schemas (Phase 14)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.property import PropertySummaryRead


class ResidentialComplexBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=255)
    developer_name: str | None = Field(None, max_length=200)
    status: str = Field(
        default="under_construction",
        pattern="^(announced|under_construction|ready)$",
    )
    description: str | None = None
    address_text: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=100)
    district: str | None = Field(None, max_length=100)
    metro: str | None = Field(None, max_length=100)
    latitude: float | None = None
    longitude: float | None = None
    completion_year: int | None = Field(None, ge=1900, le=2100)
    total_units: int | None = Field(None, ge=0)
    cover_image: str | None = Field(None, max_length=500)
    amenities: list[str] = Field(default_factory=list)
    is_verified: bool = False


class ResidentialComplexCreate(ResidentialComplexBase):
    pass


class ResidentialComplexUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    slug: str | None = Field(None, min_length=2, max_length=255)
    developer_name: str | None = Field(None, max_length=200)
    status: str | None = Field(None, pattern="^(announced|under_construction|ready)$")
    description: str | None = None
    address_text: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=100)
    district: str | None = Field(None, max_length=100)
    metro: str | None = Field(None, max_length=100)
    latitude: float | None = None
    longitude: float | None = None
    completion_year: int | None = Field(None, ge=1900, le=2100)
    total_units: int | None = Field(None, ge=0)
    cover_image: str | None = Field(None, max_length=500)
    amenities: list[str] | None = None
    is_verified: bool | None = None


class ResidentialComplexRead(ResidentialComplexBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    properties_count: int = 0
    units_available: int = 0
    created_at: datetime
    updated_at: datetime


class ResidentialComplexDetail(ResidentialComplexRead):
    properties: list[PropertySummaryRead] = []
