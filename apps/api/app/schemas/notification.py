from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    title: str = Field(..., max_length=200)
    message: str = Field(...)
    is_read: bool = False
    kind: str = "general"
    link: str | None = None


class NotificationCreate(NotificationBase):
    user_id: uuid.UUID


class NotificationUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    message: str | None = None
    is_read: bool | None = None
    kind: str | None = None
    link: str | None = None


class NotificationRead(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class NotificationUnreadCount(BaseModel):
    unread: int = 0
