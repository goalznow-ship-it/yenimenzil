from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AgentBase(BaseModel):
    name: str = Field(..., max_length=150)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=32)
    avatar_url: HttpUrl | None = None
    verified_identity: bool = False
    verified_phone: bool = False
    member_since: datetime | None = None


class AgentCreate(AgentBase):
    user_id: uuid.UUID | None = None
    agency_id: uuid.UUID | None = None


class AgentUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=32)
    avatar_url: HttpUrl | None = None
    verified_identity: bool | None = None
    verified_phone: bool | None = None
    member_since: datetime | None = None
    user_id: uuid.UUID | None = None
    agency_id: uuid.UUID | None = None


class AgentRead(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None = None
    agency_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
