from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

PROMOTION_TIERS: dict[str, dict] = {
    "standard": {"price": 500, "days": 7, "label": "STANDARD"},
    "premium": {"price": 1500, "days": 14, "label": "PREMIUM"},
    "vip": {"price": 3000, "days": 30, "label": "VIP"},
    "top": {"price": 5000, "days": 30, "label": "TOP"},
    "urgent": {"price": 7000, "days": 7, "label": "URGENT"},
}


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


class TopUpRequest(BaseModel):
    amount: int = Field(ge=100, le=1_000_000)
    note: str | None = Field(None, max_length=200)


class TopUpRead(BaseModel):
    transaction: WalletTransactionRead
    detail: str = "Pending confirmation. Credits will be added once confirmed."


class PromotionCatalogItem(BaseModel):
    tier: str
    label: str
    price: int
    days: int
    description: str


class PromotionPurchaseRequest(BaseModel):
    property_id: uuid.UUID
    tier: str


class PromotionPurchaseRead(BaseModel):
    transaction: WalletTransactionRead
    promotion_status: str
    expires_at: datetime | None = None
    detail: str = "Promotion activated"


class AdminConfirmTopUpRequest(BaseModel):
    approve: bool = True
    note: str | None = Field(None, max_length=200)
