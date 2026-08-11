from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AgencyBase(BaseModel):
    name: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=220)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=32)
    website: HttpUrl | None = None
    logo_url: HttpUrl | None = None
    description: str | None = None
    is_verified: bool = False


class AgencyCreate(AgencyBase):
    pass


class AgencyUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    slug: str | None = Field(None, max_length=220)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=32)
    website: HttpUrl | None = None
    logo_url: HttpUrl | None = None
    description: str | None = None
    is_verified: bool | None = None


class AgencyRead(AgencyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
