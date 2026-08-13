from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    avatar_url: str | None = None


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    is_read: bool
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID | None = None
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    last_message_at: datetime | None = None
    buyer_archived: bool = False
    seller_archived: bool = False
    buyer_blocked: bool = False
    seller_blocked: bool = False
    created_at: datetime
    buyer: MessageUserRead
    seller: MessageUserRead
    property_title: str | None = None
    property_cover: str | None = None
    unread_count: int = 0
    last_message: str | None = None


class ConversationCreate(BaseModel):
    property_id: uuid.UUID
    message: str = Field(min_length=1, max_length=4000)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class UnreadCountsRead(BaseModel):
    total: int = 0
    conversations: int = 0
