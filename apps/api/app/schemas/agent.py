from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.enums import Currency


class AgentBase(BaseModel):
    name: str = Field(..., max_length=150)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=32)
    avatar_url: Optional[HttpUrl] = None
    verified_identity: bool = False
    verified_phone: bool = False
    member_since: Optional[datetime] = None


class AgentCreate(AgentBase):
    user_id: Optional[uuid.UUID] = None
    agency_id: Optional[uuid.UUID] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=32)
    avatar_url: Optional[HttpUrl] = None
    verified_identity: Optional[bool] = None
    verified_phone: Optional[bool] = None
    member_since: Optional[datetime] = None
    user_id: Optional[uuid.UUID] = None
    agency_id: Optional[uuid.UUID] = None


class AgentRead(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    agency_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
