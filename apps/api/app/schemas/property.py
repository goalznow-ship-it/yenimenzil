import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    BuildingType,
    Currency,
    DealType,
    DocumentType,
    FeatureKind,
    MediaKind,
    PropertyStatus,
    PropertyType,
    RepairStatus,
    SellerKind,
)


class PropertyLocationCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address_text: str = ""
    city: str | None = None
    district: str | None = None
    settlement: str | None = None
    neighborhood: str | None = None
    metro: str | None = None


class PropertyMediaCreate(BaseModel):
    url: str = Field(min_length=1, max_length=1000)
    alt: str | None = Field(default=None, max_length=300)
    placeholder: str | None = Field(default=None, max_length=500)
    sort_order: int = 0
    is_cover: bool = False


class PropertyPriceHistoryCreate(BaseModel):
    price: float
    recorded_at: datetime | None = None


class PropertyBase(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    description: str = ""
    deal_type: DealType
    property_type: PropertyType
    price: float = Field(gt=0)
    currency: Currency = Currency.AZN
    rooms: int = Field(default=0, ge=0)
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    area_total: float = Field(gt=0)
    area_living: float | None = Field(default=None, gt=0)
    area_land: float | None = Field(default=None, gt=0)
    floor: int | None = Field(default=None, ge=0)
    total_floors: int | None = Field(default=None, ge=0)
    building_type: BuildingType | None = None
    repair_status: RepairStatus | None = None
    document_type: DocumentType | None = None
    mortgage_available: bool = False


class PropertyCreate(PropertyBase):
    owner_id: uuid.UUID
    agency_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    seller_kind: SellerKind = SellerKind.OWNER
    status: PropertyStatus = PropertyStatus.ACTIVE
    is_verified: bool = False
    is_premium: bool = False
    is_promoted: bool = False
    location: PropertyLocationCreate
    media: list[PropertyMediaCreate] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    price_history: list[PropertyPriceHistoryCreate] = Field(default_factory=list)

    @field_validator("features")
    @classmethod
    def validate_feature_codes(cls, v: list[str]) -> list[str]:
        known = {feature.value for feature in __import__("app.models.enums", fromlist=["FeatureKind"]).FeatureKind}
        unknown = set(v) - known
        if unknown:
            raise ValueError(f"unknown feature codes: {sorted(unknown)}")
        return v


class PropertyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=300)
    description: str | None = None
    deal_type: DealType | None = None
    property_type: PropertyType | None = None
    price: float | None = Field(default=None, gt=0)
    currency: Currency | None = None
    rooms: int | None = Field(default=None, ge=0)
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    area_total: float | None = Field(default=None, gt=0)
    area_living: float | None = Field(default=None, gt=0)
    area_land: float | None = Field(default=None, gt=0)
    floor: int | None = Field(default=None, ge=0)
    total_floors: int | None = Field(default=None, ge=0)
    building_type: BuildingType | None = None
    repair_status: RepairStatus | None = None
    document_type: DocumentType | None = None
    mortgage_available: bool | None = None
    status: PropertyStatus | None = None
    seller_kind: SellerKind | None = None
    is_verified: bool | None = None
    is_premium: bool | None = None
    is_promoted: bool | None = None
    agency_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    location: PropertyLocationCreate | None = None
    media: list[PropertyMediaCreate] | None = None
    features: list[str] | None = None


class PropertyMediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: MediaKind
    url: str
    alt: str | None
    placeholder: str | None
    sort_order: int
    is_cover: bool


class PropertyLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    latitude: float
    longitude: float
    address_text: str
    city: str | None
    district: str | None
    settlement: str | None
    neighborhood: str | None
    metro: str | None


class PropertyPriceHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    price: float
    recorded_at: datetime


class PropertySummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference_code: str
    slug: str
    title: str
    deal_type: DealType
    property_type: PropertyType
    building_type: BuildingType | None
    repair_status: RepairStatus | None
    price: float
    currency: Currency
    price_per_sqm: float | None
    rooms: int
    area_total: float
    floor: int | None
    total_floors: int | None
    is_verified: bool
    is_premium: bool
    is_promoted: bool
    status: PropertyStatus
    published_at: datetime | None
    city: str | None
    district: str | None
    cover_image: str | None
    image_count: int
    has_price_drop: bool


class PropertyRead(PropertySummaryRead):
    description: str
    bedrooms: int | None
    bathrooms: int | None
    area_living: float | None
    area_land: float | None
    document_type: DocumentType | None
    mortgage_available: bool
    seller_kind: SellerKind
    owner_id: uuid.UUID
    agency_id: uuid.UUID | None
    agent_id: uuid.UUID | None
    views: int
    created_at: datetime
    updated_at: datetime
    features: list[str]
    location: PropertyLocationRead | None
    media: list[PropertyMediaRead]
    price_history: list[PropertyPriceHistoryRead]
