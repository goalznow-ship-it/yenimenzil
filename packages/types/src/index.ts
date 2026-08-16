export type DealType = "sale" | "rent" | "daily";

export type PropertyType =
  | "apartment"
  | "new_building"
  | "old_building"
  | "house"
  | "villa"
  | "land"
  | "office"
  | "commercial"
  | "garage";

export type PropertyStatus =
  | "draft"
  | "pending_review"
  | "active"
  | "rejected"
  | "expired"
  | "sold"
  | "rented"
  | "archived"
  | "suspended";

export type Currency = "AZN" | "USD" | "EUR";

export type RepairStatus = "renovated" | "cosmetic" | "needs_repair" | "none";

export type BuildingType = "new" | "old";

export type DocumentType = "citizenship" | "extract" | "certificate";

export type SellerKind = "owner" | "agency" | "agent";

export type BadgeKind = "premium" | "new" | "price_drop" | "verified";

export type FeatureKey =
  | "extract"
  | "mortgage"
  | "gas"
  | "water"
  | "electricity"
  | "central_heating"
  | "kombi"
  | "air_conditioning"
  | "elevator"
  | "security"
  | "parking"
  | "balcony"
  | "pool"
  | "garden"
  | "furnished"
  | "internet"
  | "home_appliances"
  | "children_playground";

export interface GeoPoint {
  lat: number;
  lng: number;
}

export interface PropertyLocation {
  country: string;
  city: string;
  district: string;
  settlement?: string;
  neighborhood?: string;
  metro?: string;
  street?: string;
  addressText: string;
  point: GeoPoint;
}

export interface PriceHistoryEntry {
  date: string;
  price: number;
}

export interface ListingSeller {
  id: string;
  name: string;
  kind: SellerKind;
  agencyName?: string;
  avatarUrl?: string;
  verifiedPhone: boolean;
  verifiedIdentity: boolean;
  memberSince: string;
  activeListings: number;
}

export interface Property {
  id: string;
  referenceCode: string;
  slug: string;
  title: string;
  description: string;
  dealType: DealType;
  propertyType: PropertyType;
  buildingType?: BuildingType;
  repairStatus?: RepairStatus;
  documentType?: DocumentType;
  price: number;
  currency: Currency;
  pricePerSqm?: number;
  rooms: number;
  bedrooms?: number;
  bathrooms?: number;
  areaTotal: number;
  areaLiving?: number;
  areaLand?: number;
  floor?: number;
  totalFloors?: number;
  constructionYear?: number;
  mortgageAvailable: boolean;
  furnished?: boolean;
  heating?: string;
  features: FeatureKey[];
  location: PropertyLocation;
  images: PropertyImage[];
  badges: BadgeKind[];
  isVerified: boolean;
  isFavorite?: boolean;
  isPremium?: boolean;
  isPromoted?: boolean;
  status: PropertyStatus;
  seller: ListingSeller;
  publishedAt: string;
  views: number;
  priceHistory: PriceHistoryEntry[];
}

export interface PropertyImage {
  src: string;
  alt: string;
  placeholder?: string;
}

export interface SearchFilters {
  deal: DealType;
  city: string;
  district: string;
  propertyType: PropertyType | "all";
  rooms: number[];
  minPrice?: number;
  maxPrice?: number;
  minArea?: number;
  maxArea?: number;
  metro?: string;
  buildingType?: BuildingType;
  repairStatus?: RepairStatus;
  ownerOnly?: boolean;
  verifiedOnly?: boolean;
  withPhoto?: boolean;
  minYear?: number;
  maxYear?: number;
  minFloor?: number;
  maxFloor?: number;
  north?: number;
  south?: number;
  east?: number;
  west?: number;
  sort: SortKey;
}

export type SortKey =
  | "newest"
  | "price_asc"
  | "price_desc"
  | "area_asc"
  | "area_desc";

export type MapViewMode = "list" | "grid" | "map";

export interface MapMarkerData {
  id: string;
  point: GeoPoint;
  price: number;
  formattedPrice: string;
}

export const DEAL_LABELS: Record<DealType, string> = {
  sale: "Al",
  rent: "Kirayə",
  daily: "Günlük"
};

export const PROPERTY_TYPE_LABELS: Record<PropertyType, string> = {
  apartment: "Mənzil",
  new_building: "Yeni tikili",
  old_building: "Köhnə tikili",
  house: "Həyət evi",
  villa: "Villa",
  land: "Torpaq",
  office: "Ofis",
  commercial: "Obyekt",
  garage: "Qaraj"
};

export const FEATURE_LABELS: Record<FeatureKey, string> = {
  extract: "Çıxarış",
  mortgage: "İpoteka",
  gas: "Qaz",
  water: "Su",
  electricity: "İşıq",
  central_heating: "Mərkəzi istilik",
  kombi: "Kombi",
  air_conditioning: "Kondisioner",
  elevator: "Lift",
  security: "Mühafizə",
  parking: "Parkinq",
  balcony: "Balkon",
  pool: "Hovuz",
  garden: "Həyət",
  furnished: "Mebel",
  internet: "İnternet",
  home_appliances: "Məişət texnikası",
  children_playground: "Uşaq meydançası"
};

export const REPAIR_LABELS: Record<RepairStatus, string> = {
  renovated: "Təmirli",
  cosmetic: "Kosmetik təmir",
  needs_repair: "Təmir tələb olunur",
  none: "Təmirsiz"
};

export const BUILDING_TYPE_LABELS: Record<BuildingType, string> = {
  new: "Yeni tikili",
  old: "Köhnə tikili"
};

export type ComplexStatus = "announced" | "under_construction" | "ready";

export interface ResidentialComplex {
  id: string;
  name: string;
  slug: string;
  developerName?: string;
  status: ComplexStatus;
  description?: string;
  addressText?: string;
  city?: string;
  district?: string;
  metro?: string;
  latitude?: number;
  longitude?: number;
  completionYear?: number;
  totalUnits?: number;
  coverImage?: string;
  amenities: string[];
  isVerified: boolean;
  propertiesCount: number;
  unitsAvailable: number;
  createdAt: string;
}

export interface ComplexDetail extends ResidentialComplex {
  properties: Property[];
}

export const COMPLEX_STATUS_LABELS: Record<ComplexStatus, string> = {
  announced: "Elan edilib",
  under_construction: "Tikilir",
  ready: "Hazırdır"
};
