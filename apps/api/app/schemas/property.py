import uuid
from datetime import datetime

from fastapi import Query
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
    StrEnum,
)

KNOWN_FEATURE_CODES = {feature.value for feature in FeatureKind}


class PropertyLocationCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address_text: str = ""
    city: str | None = None
    district: str | None = None
    settlement: str | None = None
    neighborhood: str | None = None
    metro: str | None = None
    landmark: str | None = Field(default=None, max_length=150)
    street: str | None = Field(default=None, max_length=150)


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
    owner_id: uuid.UUID | None = None
    agency_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    seller_kind: SellerKind = SellerKind.OWNER
    status: PropertyStatus = PropertyStatus.DRAFT
    is_verified: bool = False
    is_premium: bool = False
    is_promoted: bool = False
    construction_year: int | None = Field(default=None, ge=1900, le=2100)
    heating: str | None = Field(default=None, max_length=120)
    furnished: bool = False
    location: PropertyLocationCreate
    media: list[PropertyMediaCreate] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    price_history: list[PropertyPriceHistoryCreate] = Field(default_factory=list)

    @field_validator("features")
    @classmethod
    def validate_feature_codes(cls, v: list[str]) -> list[str]:
        unknown = set(v) - KNOWN_FEATURE_CODES
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
    furnished: bool | None = None
    heating: str | None = Field(default=None, max_length=120)
    construction_year: int | None = Field(default=None, ge=1900, le=2100)
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

    @field_validator("features")
    @classmethod
    def validate_feature_codes(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        unknown = set(v) - KNOWN_FEATURE_CODES
        if unknown:
            raise ValueError(f"unknown feature codes: {sorted(unknown)}")
        return v


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
    landmark: str | None
    street: str | None


class PropertyPriceHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    price: float
    recorded_at: datetime


class PropertySellerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    kind: SellerKind
    agency_name: str | None
    avatar_url: str | None
    phone: str | None
    verified_phone: bool
    verified_identity: bool
    member_since: str | None
    active_listings: int


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
    promotion_tier: str | None = None
    promotion_expires_at: datetime | None = None
    status: PropertyStatus
    published_at: datetime | None
    city: str | None
    district: str | None
    address_text: str | None
    metro: str | None
    latitude: float | None
    longitude: float | None
    cover_image: str | None
    image_count: int
    has_price_drop: bool
    seller: PropertySellerRead


class PropertyRead(PropertySummaryRead):
    description: str
    bedrooms: int | None
    bathrooms: int | None
    area_living: float | None
    area_land: float | None
    document_type: DocumentType | None
    mortgage_available: bool
    furnished: bool
    heating: str | None
    construction_year: int | None
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


class PropertySort(StrEnum):
    NEWEST = "newest"
    OLDEST = "oldest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    PRICE_PER_M2_ASC = "price_per_m2_asc"
    PRICE_PER_M2_DESC = "price_per_m2_desc"
    AREA_ASC = "area_asc"
    AREA_DESC = "area_desc"
    VIEWS = "views"
    FAVORITES = "favorites"


class PropertyQueryParams(BaseModel):
    """Query parameters accepted by GET /properties.

    Mirrors the frontend URL filters in apps/web/src/features/search/use-search-filters.ts.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    # filters
    deal: DealType = DealType.SALE
    city: str | None = None
    district: str | None = None
    property_type: PropertyType | None = Field(default=None, alias="property_type")
    rooms: list[int] = Query(default=[])
    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)
    min_area: float | None = Field(default=None, ge=0)
    max_area: float | None = Field(default=None, ge=0)
    min_area_land: float | None = Field(default=None, ge=0)
    max_area_land: float | None = Field(default=None, ge=0)
    metro: str | None = None
    landmark: str | None = None
    building_type: BuildingType | None = None
    repair_status: RepairStatus | None = None
    owner_only: bool = False
    verified_only: bool = False
    promoted_only: bool = False
    price_dropped: bool = False
    mortgage: bool | None = None
    furnished: bool | None = None
    heating: str | None = None
    document_type: DocumentType | None = None
    floor: int | None = Field(default=None, ge=0)
    total_floors: int | None = Field(default=None, ge=0)
    is_first_floor: bool = False
    is_last_floor: bool = False
    min_bedrooms: int | None = Field(default=None, ge=0)
    max_bedrooms: int | None = Field(default=None, ge=0)
    min_bathrooms: int | None = Field(default=None, ge=0)
    max_bathrooms: int | None = Field(default=None, ge=0)
    min_construction_year: int | None = Field(default=None, ge=1900, le=2100)
    max_construction_year: int | None = Field(default=None, ge=1900, le=2100)
    seller_kind: SellerKind | None = None
    agent_id: uuid.UUID | None = None
    agency_id: uuid.UUID | None = None
    keyword: str | None = None
    published_after: datetime | None = None
    features: list[str] = Query(default=[])

    # map bounding box (east/west can wrap the antimeridian, so no le/ge here)
    north: float | None = Field(default=None, ge=-90, le=90)
    south: float | None = Field(default=None, ge=-90, le=90)
    east: float | None = None
    west: float | None = None

    # sorting + pagination
    sort: PropertySort = PropertySort.NEWEST
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=30, ge=1, le=100)

    @field_validator("rooms", mode="before")
    @classmethod
    def split_rooms(cls, v: object) -> object:
        # Accept comma-separated ("1,2,4plus") or repeated query params.
        # FastAPI hands list-typed query params to the model as a list, so
        # handle both plain strings and sequences of raw values.
        if isinstance(v, str):
            parts = v.split(",")
        elif isinstance(v, (list, tuple, set, frozenset)):
            parts = []
            for item in v:
                parts.extend(str(item).split(","))
        else:
            return v
        out: list[int] = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part == "4plus":
                out.append(4)
                continue
            try:
                out.append(int(part))
            except ValueError:
                continue
        return out

    @field_validator("features", mode="before")
    @classmethod
    def split_features(cls, v: object) -> object:
        if isinstance(v, str):
            return [p for p in v.split(",") if p]
        return v
