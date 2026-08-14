/**
 * Property data access for the frontend.
 *
 * Two modes, controlled by NEXT_PUBLIC_USE_DEMO_DATA (default "true"):
 *  - demo: serves the bundled demo listings (apps/web/src/data/listings.ts)
 *  - api:  talks to the FastAPI backend (NEXT_PUBLIC_API_URL, default
 *          http://localhost:8000/api/v1) and adapts its snake_case payloads
 *          to the camelCase Property type.
 *
 * All consumers should use the fetch* helpers below; they pick the mode
 * automatically so the app keeps working without the backend running.
 */
import type {
  BadgeKind,
  Property,
  PropertyType,
  SearchFilters,
  SortKey
} from "@yenimenzil/types";
import {
  filterListings,
  getFeaturedSections,
  getListingById,
  getPremiumListings,
  getSimilarListings,
  sortListings
} from "@/services/listings-service";
import { getDemoListings } from "@/data/listings";

export const API_URL =
  typeof window === "undefined"
    ? process.env.API_INTERNAL_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      "http://localhost:8000/api/v1"
    : process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export const USE_DEMO_DATA =
  (process.env.NEXT_PUBLIC_USE_DEMO_DATA ?? "true") !== "false";

// ── API DTOs (snake_case, mirroring app/schemas/property.py) ──────────────

interface ApiPaginationMeta {
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

interface ApiPaginated<T> {
  data: T[];
  meta: ApiPaginationMeta;
}

interface ApiSeller {
  id: string;
  name: string;
  kind: "owner" | "agency" | "agent";
  agency_name: string | null;
  avatar_url: string | null;
  phone: string | null;
  verified_phone: boolean;
  verified_identity: boolean;
  member_since: string | null;
  active_listings: number;
}

interface ApiLocation {
  latitude: number;
  longitude: number;
  address_text: string;
  city: string | null;
  district: string | null;
  settlement: string | null;
  neighborhood: string | null;
  metro: string | null;
}

interface ApiMedia {
  url: string;
  alt: string | null;
  placeholder: string | null;
  is_cover: boolean;
}

interface ApiPriceHistory {
  price: number;
  recorded_at: string;
}

interface ApiListing {
  id: string;
  reference_code: string;
  slug: string;
  title: string;
  description?: string;
  deal_type: "sale" | "rent" | "daily";
  property_type: PropertyType;
  building_type?: "new" | "old";
  repair_status?: "renovated" | "cosmetic" | "needs_repair" | "none";
  document_type?: "citizenship" | "extract" | "certificate";
  price: number;
  currency: "AZN" | "USD" | "EUR";
  price_per_sqm: number | null;
  rooms: number;
  bedrooms?: number | null;
  bathrooms?: number | null;
  area_total: number;
  area_living?: number | null;
  area_land?: number | null;
  floor?: number | null;
  total_floors?: number | null;
  construction_year?: number | null;
  mortgage_available?: boolean;
  furnished?: boolean;
  heating?: string | null;
  features?: string[];
  status: Property["status"];
  is_verified: boolean;
  is_premium?: boolean;
  is_promoted?: boolean;
  published_at: string | null;
  views?: number;
  has_price_drop?: boolean;
  city?: string | null;
  district?: string | null;
  address_text?: string | null;
  metro?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  cover_image?: string | null;
  image_count?: number;
  seller?: ApiSeller;
  location?: ApiLocation | null;
  media?: ApiMedia[];
  price_history?: ApiPriceHistory[];
}

// ── Adapter ────────────────────────────────────────────────────────────────

const NEW_BADGE_WINDOW_MS = 14 * 24 * 60 * 60 * 1000;

export function toProperty(api: ApiListing): Property {
  const location = api.location;
  const media = api.media ?? [];
  const images = media
    .filter((m) => m.url)
    .map((m) => ({
      src: m.url,
      alt: m.alt ?? "",
      placeholder: m.placeholder ?? undefined
    }));
  if (images.length === 0 && api.cover_image) {
    images.push({ src: api.cover_image, alt: "", placeholder: undefined });
  }

  const badges: BadgeKind[] = [];
  if (api.is_premium) badges.push("premium");
  if (api.has_price_drop) badges.push("price_drop");
  if (api.is_verified) badges.push("verified");
  const publishedMs = api.published_at
    ? Date.parse(api.published_at)
    : Date.now();
  if (Number.isFinite(publishedMs) && Date.now() - publishedMs < NEW_BADGE_WINDOW_MS) {
    badges.push("new");
  }

  const seller: Property["seller"] = {
    id: api.seller?.id ?? api.id,
    name: api.seller?.name ?? "Elan sahibi",
    kind: api.seller?.kind ?? "owner",
    agencyName: api.seller?.agency_name ?? undefined,
    avatarUrl: api.seller?.avatar_url ?? undefined,
    verifiedPhone: api.seller?.verified_phone ?? false,
    verifiedIdentity: api.seller?.verified_identity ?? false,
    memberSince: api.seller?.member_since ?? "",
    activeListings: api.seller?.active_listings ?? 0
  };

  return {
    id: api.id,
    referenceCode: api.reference_code,
    slug: api.slug,
    title: api.title,
    description: api.description ?? "",
    dealType: api.deal_type,
    propertyType: api.property_type,
    buildingType: api.building_type,
    repairStatus: api.repair_status,
    documentType: api.document_type,
    price: Number(api.price),
    currency: api.currency,
    pricePerSqm:
      api.price_per_sqm != null ? Number(api.price_per_sqm) : undefined,
    rooms: api.rooms,
    bedrooms: api.bedrooms ?? undefined,
    bathrooms: api.bathrooms ?? undefined,
    areaTotal: Number(api.area_total),
    areaLiving: api.area_living != null ? Number(api.area_living) : undefined,
    areaLand: api.area_land != null ? Number(api.area_land) : undefined,
    floor: api.floor ?? undefined,
    totalFloors: api.total_floors ?? undefined,
    constructionYear: api.construction_year ?? undefined,
    mortgageAvailable: api.mortgage_available ?? false,
    furnished: api.furnished ?? false,
    heating: api.heating ?? undefined,
    features: (api.features ?? []) as Property["features"],
    location: {
      country: "Azərbaycan",
      city: api.city ?? location?.city ?? "",
      district: api.district ?? location?.district ?? "",
      settlement: location?.settlement ?? undefined,
      neighborhood: location?.neighborhood ?? undefined,
      metro: api.metro ?? location?.metro ?? undefined,
      addressText: api.address_text ?? location?.address_text ?? "",
      point: {
        lat: location?.latitude ?? api.latitude ?? 0,
        lng: location?.longitude ?? api.longitude ?? 0
      }
    },
    images,
    badges,
    isVerified: api.is_verified,
    isPremium: api.is_premium ?? false,
    isPromoted: api.is_promoted ?? false,
    status: api.status,
    seller,
    publishedAt: api.published_at ?? new Date().toISOString(),
    views: api.views ?? 0,
    priceHistory: (api.price_history ?? []).map((entry) => ({
      date: entry.recorded_at,
      price: Number(entry.price)
    }))
  };
}

// ── HTTP helpers ───────────────────────────────────────────────────────────

async function fetchJson<T>(path: string, params?: URLSearchParams): Promise<T> {
  const url = params ? `${API_URL}${path}?${params.toString()}` : `${API_URL}${path}`;
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API ${response.status} for ${url}`);
  }
  return (await response.json()) as T;
}

function toSearchParams(filters: Partial<SearchFilters>): URLSearchParams {
  const params = new URLSearchParams();
  const set = (key: string, value?: string | number | boolean | null) => {
    if (value !== undefined && value !== null && value !== "" && value !== "all") {
      params.set(key, String(value));
    }
  };
  set("deal", filters.deal);
  set("city", filters.city);
  set("district", filters.district);
  set("property_type", filters.propertyType);
  if (filters.rooms && filters.rooms.length > 0) {
    params.set(
      "rooms",
      filters.rooms.map((r) => (r >= 4 ? "4plus" : String(r))).join(",")
    );
  }
  set("min_price", filters.minPrice);
  set("max_price", filters.maxPrice);
  set("min_area", filters.minArea);
  set("max_area", filters.maxArea);
  set("metro", filters.metro);
  set("building_type", filters.buildingType);
  set("repair_status", filters.repairStatus);
  set("owner_only", filters.ownerOnly);
  set("verified_only", filters.verifiedOnly);
  set("with_photo", filters.withPhoto);
  set("min_year", filters.minYear);
  set("max_year", filters.maxYear);
  set("min_floor", filters.minFloor);
  set("max_floor", filters.maxFloor);
  set("sort", filters.sort);
  return params;
}

// ── Public API (mode-aware) ────────────────────────────────────────────────

export interface SearchResult {
  data: Property[];
  total: number;
  page: number;
  pages: number;
}

export async function searchProperties(
  filters: Partial<SearchFilters>
): Promise<SearchResult> {
  if (USE_DEMO_DATA) {
    const data = sortListings(filterListings(filters), filters.sort ?? "newest");
    return { data, total: data.length, page: 1, pages: 1 };
  }
  const params = toSearchParams(filters);
  params.set("page", "1");
  params.set("page_size", "100");
  const body = await fetchJson<ApiPaginated<ApiListing>>("/properties", params);
  return {
    data: body.data.map(toProperty),
    total: body.meta.total,
    page: body.meta.page,
    pages: body.meta.pages
  };
}

export async function fetchPropertyById(
  id: string,
  source: Property[] = getDemoListings()
): Promise<Property | undefined> {
  if (USE_DEMO_DATA) return getListingById(id, source);
  try {
    const body = await fetchJson<ApiListing>(`/properties/${id}`);
    return toProperty(body);
  } catch {
    return undefined;
  }
}

export async function fetchSimilarProperties(
  listing: Property,
  limit = 4
): Promise<Property[]> {
  if (USE_DEMO_DATA) return getSimilarListings(listing, limit);
  try {
    const body = await fetchJson<ApiListing[]>(
      `/properties/${listing.id}/similar?limit=${limit}`
    );
    return body.map(toProperty);
  } catch {
    return [];
  }
}

export async function fetchPremiumProperties(limit = 8): Promise<Property[]> {
  if (USE_DEMO_DATA) return getPremiumListings(limit);
  try {
    const body = await searchProperties({ deal: "sale", sort: "newest" });
    return body.data.filter((p) => p.isPremium || p.isPromoted).slice(0, limit);
  } catch {
    return [];
  }
}

export interface FeaturedSections {  all: Property[];
  newest: Property[];
  premium: Property[];
  priceDropped: Property[];
  popular: Property[];
  newBuildings: Property[];
  nearMetro: Property[];
  seaside: Property[];
  family: Property[];
  villas: Property[];
  land: Property[];
  commercial: Property[];
}

export async function fetchFeaturedSections(): Promise<FeaturedSections> {
  if (USE_DEMO_DATA) {
    return { all: getDemoListings(), ...getFeaturedSections() };
  }
  const all = await searchProperties({ deal: "sale", sort: "newest" });
  const list = all.data;
  return {
    all: list,
    newest: [...list].sort(
      (a, b) => +new Date(b.publishedAt) - +new Date(a.publishedAt)
    ),
    premium: list.filter((p) => p.isPremium || p.isPromoted),
    priceDropped: list.filter((p) => p.priceHistory.length >= 2),
    popular: list
      .filter((p) => p.views > 300)
      .sort((a, b) => b.views - a.views)
      .slice(0, 8),
    newBuildings: list.filter(
      (p) => p.propertyType === "new_building" && p.dealType === "sale"
    ),
    nearMetro: list.filter((p) => p.location.metro),
    seaside: list.filter(
      (p) =>
        p.location.district === "Xəzər" ||
        p.location.district === "Səbail"
    ),
    family: list.filter((p) => p.rooms >= 3 && p.dealType === "sale"),
    villas: list.filter((p) => p.propertyType === "villa"),
    land: list.filter((p) => p.propertyType === "land"),
    commercial: list.filter(
      (p) =>
        p.propertyType === "office" ||
        p.propertyType === "commercial" ||
        p.propertyType === "garage"
    )
  };
}

/**
 * Market pool for price intelligence: listings of the same deal + type.
 * Falls back to the demo pool when the API is unreachable.
 */
export async function fetchMarketPool(
  property: Property
): Promise<Property[]> {
  if (USE_DEMO_DATA) {
    return getDemoListings().filter(
      (p) =>
        p.id !== property.id &&
        p.dealType === property.dealType &&
        p.propertyType === property.propertyType &&
        p.pricePerSqm != null &&
        property.pricePerSqm != null
    );
  }
  try {
    const body = await searchProperties({
      deal: property.dealType,
      propertyType: property.propertyType,
      sort: "newest" as SortKey
    });
    return body.data.filter((p) => p.id !== property.id);
  } catch {
    return [];
  }
}

/**
 * Fetch all active properties for sitemap generation.
 * Limited to reasonable number for sitemap size.
 */
export async function fetchAllProperties(options: { limit?: number } = {}): Promise<Property[]> {
  const { limit = 50000 } = options;
  if (USE_DEMO_DATA) {
    return getDemoListings().filter((p) => p.status === "active").slice(0, limit);
  }
  try {
    // Fetch in batches of 1000
    const batchSize = 1000;
    const allProperties: Property[] = [];
    let page = 1;

    while (allProperties.length < limit) {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("page_size", String(batchSize));
      params.set("status", "active");

      const response = await fetch(`${API_URL}/properties?${params.toString()}`, { cache: "no-store" });
      if (!response.ok) break;

      const body = await response.json() as ApiPaginated<ApiListing>;
      const properties = body.data.map(toProperty);
      if (properties.length === 0) break;

      allProperties.push(...properties);
      if (page >= body.meta.pages) break;
      page++;
    }
    return allProperties.slice(0, limit);
  } catch {
    return [];
  }
}

// ── Agent / Agency public profiles ─────────────────────────────────────────

export interface AgentProfile {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  avatar_url: string | null;
  verified_identity: boolean;
  verified_phone: boolean;
  member_since: string | null;
  agency_id: string | null;
}

export interface AgencyProfile {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  logo_url: string | null;
  verified: boolean;
  member_since: string | null;
  description: string | null;
  website: string | null;
}

export interface AgentProfileData {
  agent: AgentProfile;
  listings: Property[];
  is_favorite: boolean;
  is_mine?: boolean;
}

export interface AgencyProfileData {
  agency: AgencyProfile;
  listings: Property[];
  agents: AgentProfile[];
  is_favorite: boolean;
}

export async function fetchAgentProfile(agentId: string): Promise<AgentProfileData | null> {
  try {
    const body = await fetchJson<{
      agent: AgentProfile;
      listings: ApiPaginated<ApiListing>;
      is_favorite: boolean;
      is_mine?: boolean;
    }>(`/agents/${agentId}/public`);
    return {
      agent: body.agent,
      listings: body.listings.data.map(toProperty),
      is_favorite: body.is_favorite,
      is_mine: body.is_mine
    };
  } catch {
    return null;
  }
}

export async function fetchAgencyProfile(agencyId: string): Promise<AgencyProfileData | null> {
  try {
    const body = await fetchJson<{
      agency: AgencyProfile;
      listings: ApiPaginated<ApiListing>;
      agents: AgentProfile[];
      is_favorite: boolean;
    }>(`/agencies/${agencyId}/public`);
    return {
      agency: body.agency,
      listings: body.listings.data.map(toProperty),
      agents: body.agents,
      is_favorite: body.is_favorite
    };
  } catch {
    return null;
  }
}
