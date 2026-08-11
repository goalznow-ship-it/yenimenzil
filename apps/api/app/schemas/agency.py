from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.enums import Currency


class AgencyBase(BaseModel):
    name: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=220)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=32)
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    is_verified: bool = False


class AgencyCreate(AgencyBase):
    pass


class AgencyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    slug: Optional[str] = Field(None, max_length=220)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=32)
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    is_verified: Optional[bool] = None


class AgencyRead(AgencyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
