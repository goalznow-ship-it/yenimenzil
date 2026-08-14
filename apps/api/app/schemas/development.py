import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class DeveloperCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=220, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    logo_url: str | None = None
    cover_url: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    is_verified: bool = False


class DeveloperRead(DeveloperCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime


class UnitTypeInput(BaseModel):
    rooms: int = Field(ge=0, le=20)
    area_from: float = Field(gt=0)
    area_to: float | None = Field(default=None, gt=0)
    price_from: float | None = Field(default=None, ge=0)
    available_count: int = Field(default=0, ge=0)
    plan_url: str | None = None


class UnitTypeRead(UnitTypeInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class ComplexCreate(BaseModel):
    developer_id: uuid.UUID
    name: str = Field(min_length=2, max_length=220)
    slug: str = Field(min_length=2, max_length=240, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    city: str = "Bakı"
    district: str | None = None
    address: str = Field(min_length=3, max_length=500)
    latitude: float | None = None
    longitude: float | None = None
    delivery_date: date | None = None
    delivery_status: str = "construction"
    min_price: float | None = Field(default=None, ge=0)
    price_per_sqm_from: float | None = Field(default=None, ge=0)
    currency: str = "AZN"
    cover_url: str | None = None
    gallery: list[str] = Field(default_factory=list)
    amenities: list[str] = Field(default_factory=list)
    payment_terms: str | None = None
    buildings_count: int | None = Field(default=None, ge=0)
    is_featured: bool = False
    is_published: bool = False
    unit_types: list[UnitTypeInput] = Field(default_factory=list)


class ComplexUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    address: str | None = None
    delivery_date: date | None = None
    delivery_status: str | None = None
    min_price: float | None = None
    price_per_sqm_from: float | None = None
    cover_url: str | None = None
    gallery: list[str] | None = None
    amenities: list[str] | None = None
    payment_terms: str | None = None
    is_featured: bool | None = None
    is_published: bool | None = None


class ComplexRead(ComplexCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    developer: DeveloperRead
    unit_types: list[UnitTypeRead]
    created_at: datetime
