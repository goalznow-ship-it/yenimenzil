from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    BuildingType,
    Currency,
    DealType,
    DocumentType,
    MediaKind,
    PropertyStatus,
    PropertyType,
    RepairStatus,
    SellerKind,
)

if TYPE_CHECKING:
    from app.models.agency import Agency, Agent
    from app.models.analytics import AnalyticsEvent
    from app.models.favorite import Favorite
    from app.models.moderation import ModerationLog
    from app.models.report import Report
    from app.models.user import User


def _enum(enum_cls) -> Enum:
    return Enum(enum_cls, native_enum=False, length=32)


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    reference_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    agency_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    seller_kind: Mapped[SellerKind] = mapped_column(
        _enum(SellerKind), default=SellerKind.OWNER.value, nullable=False
    )

    deal_type: Mapped[DealType] = mapped_column(_enum(DealType), index=True)
    property_type: Mapped[PropertyType] = mapped_column(_enum(PropertyType), index=True)
    status: Mapped[PropertyStatus] = mapped_column(
        _enum(PropertyStatus), default=PropertyStatus.ACTIVE.value, index=True
    )
    currency: Mapped[Currency] = mapped_column(
        _enum(Currency), default=Currency.AZN.value, nullable=False
    )

    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")

    price: Mapped[float] = mapped_column(Numeric(14, 2))

    rooms: Mapped[int] = mapped_column(Integer, default=0)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    area_total: Mapped[float] = mapped_column(Numeric(10, 2))
    area_living: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    area_land: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_floors: Mapped[int | None] = mapped_column(Integer, nullable=True)

    building_type: Mapped[BuildingType | None] = mapped_column(
        _enum(BuildingType), nullable=True
    )
    repair_status: Mapped[RepairStatus | None] = mapped_column(
        _enum(RepairStatus), nullable=True
    )
    document_type: Mapped[DocumentType | None] = mapped_column(
        _enum(DocumentType), nullable=True
    )

    mortgage_available: Mapped[bool] = mapped_column(Boolean, default=False)
    furnished: Mapped[bool] = mapped_column(Boolean, default=False)
    heating: Mapped[str | None] = mapped_column(String(120), nullable=True)
    construction_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    views: Mapped[int] = mapped_column(Integer, default=0)

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    edit_count: Mapped[int] = mapped_column(Integer, server_default="0", default=0)
    last_edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[User] = relationship(back_populates="properties")
    agency: Mapped[Agency | None] = relationship(back_populates="properties")
    agent: Mapped[Agent | None] = relationship(back_populates="properties")

    location: Mapped[PropertyLocation] = relationship(
        back_populates="property", uselist=False, cascade="all, delete-orphan"
    )
    media: Mapped[list[PropertyMedia]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan",
        order_by="PropertyMedia.sort_order",
    )
    price_history: Mapped[list[PropertyPriceHistory]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan",
        order_by="PropertyPriceHistory.recorded_at",
    )
    features: Mapped[list[PropertyFeature]] = relationship(
        secondary="property_feature_items",
        back_populates="properties",
        lazy="selectin",
    )
    favorites: Mapped[list[Favorite]] = relationship(back_populates="property")
    moderation_logs: Mapped[list[ModerationLog]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )
    reports: Mapped[list[Report]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )
    analytics_events: Mapped[list[AnalyticsEvent]] = relationship(
        back_populates="property"
    )

    __table_args__ = (
        Index("ix_properties_deal_status", "deal_type", "status"),
        Index("ix_properties_price", "price"),
        Index("ix_properties_area", "area_total"),
    )


class PropertyLocation(Base):
    __tablename__ = "property_locations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), unique=True
    )

    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    point: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
    )

    address_text: Mapped[str] = mapped_column(String(300), default="")
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    settlement: Mapped[str | None] = mapped_column(String(100), nullable=True)
    neighborhood: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metro: Mapped[str | None] = mapped_column(String(100), nullable=True)
    landmark: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    street: Mapped[str | None] = mapped_column(String(150), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    property: Mapped[Property] = relationship(back_populates="location")


class PropertyMedia(Base):
    __tablename__ = "property_media"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[MediaKind] = mapped_column(
        _enum(MediaKind), default=MediaKind.IMAGE.value, nullable=False
    )
    url: Mapped[str] = mapped_column(String(1000))
    alt: Mapped[str | None] = mapped_column(String(300), nullable=True)
    placeholder: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    property: Mapped[Property] = relationship(back_populates="media")


class PropertyPriceHistory(Base):
    __tablename__ = "property_price_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    price: Mapped[float] = mapped_column(Numeric(14, 2))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    property: Mapped[Property] = relationship(back_populates="price_history")


class PropertyFeature(Base):
    """Feature catalog (codes shared with the frontend labels)."""

    __tablename__ = "property_features"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    label_az: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    properties: Mapped[list[Property]] = relationship(
        secondary="property_feature_items", back_populates="features"
    )


class PropertyFeatureItem(Base):
    __tablename__ = "property_feature_items"

    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), primary_key=True
    )
    feature_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("property_features.id", ondelete="CASCADE"), primary_key=True
    )
