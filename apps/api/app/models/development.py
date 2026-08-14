from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Developer(Base):
    __tablename__ = "developers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    complexes: Mapped[list[ResidentialComplex]] = relationship(back_populates="developer", cascade="all, delete-orphan")


class ResidentialComplex(Base):
    __tablename__ = "residential_complexes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    developer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("developers.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False)
    slug: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(120), default="Bakı")
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str] = mapped_column(String(500))
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    delivery_status: Mapped[str] = mapped_column(String(32), default="construction")
    min_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    price_per_sqm_from: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="AZN")
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gallery: Mapped[list[str]] = mapped_column(JSON, default=list)
    amenities: Mapped[list[str]] = mapped_column(JSON, default=list)
    payment_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    buildings_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    developer: Mapped[Developer] = relationship(back_populates="complexes", lazy="selectin")
    unit_types: Mapped[list[ComplexUnitType]] = relationship(back_populates="complex", cascade="all, delete-orphan", lazy="selectin")


class ComplexUnitType(Base):
    __tablename__ = "complex_unit_types"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    complex_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("residential_complexes.id", ondelete="CASCADE"), index=True)
    rooms: Mapped[int] = mapped_column(Integer)
    area_from: Mapped[float] = mapped_column(Numeric(10, 2))
    area_to: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_from: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    available_count: Mapped[int] = mapped_column(Integer, default=0)
    plan_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    complex: Mapped[ResidentialComplex] = relationship(back_populates="unit_types")
