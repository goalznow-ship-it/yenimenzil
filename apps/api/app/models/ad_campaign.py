"""Advertising campaign model (Phase 15)."""

from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.ad_event import AdEvent
    from app.models.ad_daily_stats import AdDailyStats


class AdCampaign(Base):
    """Advertising campaign with multi-placement, scheduling, targeting, analytics."""

    __tablename__ = "ad_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    advertiser: Mapped[str] = mapped_column(String(200))

    # Placement
    placement: Mapped[str] = mapped_column(String(32), index=True)
    # LEFT_RAIL | RIGHT_RAIL | HOME_TOP_BANNER | HOME_MIDDLE_BANNER |
    # SEARCH_TOP_BANNER | SEARCH_INLINE_BANNER | SEARCH_BOTTOM_BANNER |
    # PROPERTY_SIDE_AD | PROPERTY_INLINE_AD |
    # MOBILE_TOP | MOBILE_INLINE | MOBILE_BOTTOM

    # Creatives (desktop + optional mobile)
    desktop_creative_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    mobile_creative_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    alt_text: Mapped[str | None] = mapped_column(String(300), nullable=True)
    destination_url: Mapped[str] = mapped_column(String(1000))
    open_in_new_tab: Mapped[bool] = mapped_column(Boolean, default=True)

    # Scheduling
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Targeting
    device_targeting: Mapped[str] = mapped_column(String(16), default="all")  # all | desktop | mobile
    city_targeting: Mapped[list[str]] = mapped_column(JSON, default=list)
    property_category_targeting: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Priority & state
    priority: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Counters (fast path)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    events: Mapped[list[AdEvent]] = relationship(back_populates="campaign")
    daily_stats: Mapped[list[AdDailyStats]] = relationship(back_populates="campaign")

    # Computed state property
    @property
    def state(self) -> str:
        """Derived state: DRAFT | SCHEDULED | ACTIVE | PAUSED | EXPIRED | ARCHIVED"""
        if self.archived:
            return "ARCHIVED"
        if not self.enabled:
            return "PAUSED"
        now = datetime.now(UTC)
        if self.start_at and self.start_at > now:
            return "SCHEDULED"
        if self.end_at and self.end_at < now:
            return "EXPIRED"
        return "ACTIVE"

    @property
    def ctr(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.clicks / self.impressions