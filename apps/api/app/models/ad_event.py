"""Ad impression/click event log (Phase 15)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.ad_campaign import AdCampaign


class AdEvent(Base):
    """Individual ad impression or click event for audit/dedup."""

    __tablename__ = "ad_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ad_campaigns.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(16), index=True
    )  # impression | click
    # Deduplication fields
    session_key: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Metadata
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    campaign: Mapped[AdCampaign] = relationship(back_populates="events")
