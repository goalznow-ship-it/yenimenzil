from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LocationPlace(Base):
    """Azerbaijan location catalog entry.

    Supports the full hierarchy: country -> city -> district -> settlement ->
    neighborhood -> metro -> landmark -> street. Rows are denormalized with
    city/district/metro names so every place can be matched directly during
    search regardless of its level.
    """

    __tablename__ = "location_places"
    __table_args__ = (
        UniqueConstraint("kind", "slug", name="uq_location_kind_slug"),
        Index("ix_location_kind_city", "kind", "city"),
        Index("ix_location_kind_active", "kind", "is_active"),
        Index("ix_location_name", "name_az"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    name_az: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("location_places.id", ondelete="CASCADE"), nullable=True
    )

    # Denormalized context: the city/district/metro this place belongs to.
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metro: Mapped[str | None] = mapped_column(String(100), nullable=True)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    parent: Mapped[LocationPlace | None] = relationship(
        remote_side="LocationPlace.id",
        back_populates="children",
    )
    children: Mapped[list[LocationPlace]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )
