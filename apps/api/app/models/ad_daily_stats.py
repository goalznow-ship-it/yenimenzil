"""Daily aggregated ad statistics (Phase 15)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.ad_campaign import AdCampaign


class AdDailyStats(Base):
    """Daily rollup of ad impressions/clicks per campaign."""

    __tablename__ = "ad_daily_stats"
    __table_args__ = (
        UniqueConstraint("campaign_id", "date", name="uq_ad_daily_stats_campaign_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ad_campaigns.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    unique_impressions: Mapped[int] = mapped_column(Integer, default=0)
    unique_clicks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    campaign: Mapped[AdCampaign] = relationship(back_populates="daily_stats")

    @property
    def ctr(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.clicks / self.impressions
