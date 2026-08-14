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
    CHANGES_REQUESTED = "changes_requested"


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
    OWNER = "owner"
    AGENT = "agent"
    AGENCY_ADMIN = "agency_admin"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class ReportReason(StrEnum):
    FAKE = "fake"
    SCAM = "scam"
    WRONG_PRICE = "wrong_price"
    DUPLICATE = "duplicate"
    MISLEADING = "misleading"
    EXPIRED = "expired"
    OTHER = "other"


class ReportStatus(StrEnum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ModerationAction(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    SUSPENDED = "suspended"
    ACTIVATED = "activated"
    ARCHIVED = "archived"


class AnalyticsEventType(StrEnum):
    PROPERTY_VIEW = "property_view"
    PROPERTY_FAVORITE = "property_favorite"
    PROPERTY_UNFAVORITE = "property_unfavorite"
    PHONE_REVEAL = "phone_reveal"
    WHATSAPP_CLICK = "whatsapp_click"
    MESSAGE_CLICK = "message_click"
    SEARCH = "search"
    FILTER_APPLIED = "filter_applied"
    MAP_MARKER_CLICK = "map_marker_click"
    SHARE = "share"
    COMPARE = "compare"
    SAVED_SEARCH_CREATED = "saved_search_created"
    LISTING_CREATED = "listing_created"
    LISTING_SUBMITTED = "listing_submitted"


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
    EXTRACT = "extract"
    GAS = "gas"
    WATER = "water"
    ELECTRICITY = "electricity"
    CENTRAL_HEATING = "central_heating"
    KOMBI = "kombi"
    AIR_CONDITIONING = "air_conditioning"
    HOME_APPLIANCES = "home_appliances"
    CHILDREN_PLAYGROUND = "children_playground"
