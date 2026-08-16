from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FavoriteBase(BaseModel):
    pass


class FavoriteCreate(FavoriteBase):
    property_id: uuid.UUID
    collection_id: uuid.UUID | None = None


class FavoriteUpdate(BaseModel):
    collection_id: uuid.UUID | None = None


class FavoriteRead(FavoriteBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    property_id: uuid.UUID
    collection_id: uuid.UUID | None = None
    created_at: datetime


class FavoriteCollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)


class FavoriteCollectionUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=60)


class FavoriteCollectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_default: bool
    created_at: datetime
    favorite_count: int = 0
