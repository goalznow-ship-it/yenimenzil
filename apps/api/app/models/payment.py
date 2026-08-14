from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.wallet import WalletTransaction


class PaymentStatus:
    """Payment statuses shared by all providers.

    pending -> paid | failed | cancelled
    paid    -> refunded
    """

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

    TERMINAL: ClassVar[set[str]] = {PAID, FAILED, CANCELLED, REFUNDED}


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wallet_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("wallet_transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="AZN", nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default=PaymentStatus.PENDING, nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True, index=True
    )
    checkout_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship()
    wallet_transaction: Mapped[WalletTransaction | None] = relationship()
