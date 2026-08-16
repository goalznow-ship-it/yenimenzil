from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SavedSearchBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    filters: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    email_enabled: bool = True


class SavedSearchCreate(SavedSearchBase):
    pass


class SavedSearchUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    filters: dict[str, Any] | None = None
    is_active: bool | None = None
    email_enabled: bool | None = None


class SavedSearchRead(SavedSearchBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
