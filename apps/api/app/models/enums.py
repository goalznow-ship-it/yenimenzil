import enum


class StrEnum(str, enum.Enum):
    def __str__(self) -> str:
        return self.value


class DealType(StrEnum):
    SALE = "sale"
    RENT = "rent"
    DAILY = "daily"


class PropertyType(StrEnum):
    APARTMENT = "apartment"
    NEW_BUILDING = "new_building"
    OLD_BUILDING = "old_building"
    HOUSE = "house"
    VILLA = "villa"
    LAND = "land"
    OFFICE = "office"
    COMMERCIAL = "commercial"
    GARAGE = "garage"


class PropertyStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SOLD = "sold"
    RENTED = "rented"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


class Currency(StrEnum):
    AZN = "AZN"
    USD = "USD"
    EUR = "EUR"


class RepairStatus(StrEnum):
    RENOVATED = "renovated"
    COSMETIC = "cosmetic"
    NEEDS_REPAIR = "needs_repair"
    NONE = "none"


class BuildingType(StrEnum):
    NEW = "new"
    OLD = "old"


class DocumentType(StrEnum):
    CITIZENSHIP = "citizenship"
    EXTRACT = "extract"
    CERTIFICATE = "certificate"


class SellerKind(StrEnum):
    OWNER = "owner"
    AGENCY = "agency"
    AGENT = "agent"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class MediaKind(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class FeatureKind(StrEnum):
    """Feature codes shared with the frontend feature labels."""

    ELEVATOR = "elevator"
    PARKING = "parking"
    FURNISHED = "furnished"
    BALCONY = "balcony"
    RENOVATION = "renovation"
    POOL = "pool"
    GARDEN = "garden"
    SECURITY = "security"
    INTERNET = "internet"
    CABLE_TV = "cable_tv"
    REPAIR = "repair"
    DOCUMENT = "document"
    MORTGAGE = "mortgage"
    EXCHANGE = "exchange"
    NEW = "new"
