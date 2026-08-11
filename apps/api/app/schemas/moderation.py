from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ModerationAction


class ModerationLogBase(BaseModel):
    action: ModerationAction = ModerationAction.APPROVED
    reason: str | None = Field(None, max_length=500)


class ModerationLogCreate(ModerationLogBase):
    property_id: uuid.UUID
    moderator_id: uuid.UUID


class ModerationLogRead(ModerationLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    moderator_id: uuid.UUID
    created_at: datetime
