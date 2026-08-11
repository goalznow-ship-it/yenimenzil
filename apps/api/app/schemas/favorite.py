from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FavoriteBase(BaseModel):
    pass


class FavoriteCreate(FavoriteBase):
    property_id: uuid.UUID


class FavoriteUpdate(BaseModel):
    pass


class FavoriteRead(FavoriteBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    property_id: uuid.UUID
    created_at: datetime
