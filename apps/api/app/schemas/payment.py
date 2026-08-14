from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: int
    currency: str
    status: str
    provider: str
    provider_payment_id: str | None = None
    checkout_url: str | None = None
    failure_reason: str | None = None
    note: str | None = None
    created_at: datetime
    updated_at: datetime


class TopUpRequest(BaseModel):
    amount: int = Field(ge=100, le=1_000_000)
    idempotency_key: str = Field(min_length=8, max_length=200)
    note: str | None = Field(None, max_length=200)


class TopUpRead(BaseModel):
    payment: PaymentRead
    detail: str = (
        "Payment created. Wallet is credited only after the payment is "
        "confirmed server-side (webhook or admin)."
    )


class PaymentConfirmRequest(BaseModel):
    """Admin confirmation for manual/mock payments."""

    note: str | None = Field(None, max_length=300)


class PaymentListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    amount: int
    currency: str
    status: str
    provider: str
    provider_payment_id: str | None = None
    created_at: datetime
    updated_at: datetime
