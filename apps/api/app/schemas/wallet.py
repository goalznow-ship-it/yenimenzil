from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WalletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    balance: int
    created_at: datetime


class WalletTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: int
    type: str
    status: str
    reason: str | None = None
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None
    note: str | None = None
    created_at: datetime


class PromotionCatalogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tier: str
    label: str
    price: int
    days: int
    description: str
    enabled: bool = True


class PromotionPurchaseRequest(BaseModel):
    property_id: uuid.UUID
    tier: str = Field(min_length=1, max_length=32)


class PromotionPurchaseRead(BaseModel):
    transaction: WalletTransactionRead
    promotion_status: str
    expires_at: datetime | None = None
    purchase_id: uuid.UUID | None = None
    detail: str = "Promotion activated"


class MyPromotionRead(BaseModel):
    id: uuid.UUID
    property_id: uuid.UUID
    tier: str
    label: str
    price_paid: int
    status: str
    starts_at: datetime
    ends_at: datetime
    property_title: str | None = None


class PromotionProductAdminCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32, pattern=r"^[a-z0-9_]+$")
    label_az: str = Field(min_length=2, max_length=100)
    description_az: str = Field(default="", max_length=300)
    price: int = Field(ge=1)
    duration_days: int = Field(ge=1, le=3650)
    sort_order: int = Field(default=0)
    is_premium_tier: bool = False
    enabled: bool = True


class PromotionProductAdminUpdate(BaseModel):
    label_az: str | None = Field(None, min_length=2, max_length=100)
    description_az: str | None = Field(None, max_length=300)
    price: int | None = Field(None, ge=1)
    duration_days: int | None = Field(None, ge=1, le=3650)
    sort_order: int | None = None
    is_premium_tier: bool | None = None
    enabled: bool | None = None


class PromotionProductAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    label_az: str
    description_az: str
    price: int
    duration_days: int
    sort_order: int
    is_premium_tier: bool
    enabled: bool
    created_at: datetime
    updated_at: datetime
