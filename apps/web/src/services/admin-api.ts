/**
 * Admin API client — talks to the FastAPI admin endpoints using the same
 * httpOnly cookie session as the rest of the app.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init.headers },
    ...init
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      (body && typeof body.detail === "string" && body.detail) ||
      (body && Array.isArray(body.detail)
        ? body.detail
            .map((d: { msg?: string }) => d.msg)
            .filter(Boolean)
            .join(", ")
        : null) ||
      "Xəta baş verdi";
    throw new ApiError(response.status, detail);
  }
  return body as T;
}

export interface Pagination {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface PromotedListing {
  id: string;
  title: string;
  reference_code: string;
  status: string;
  tier: string | null;
  is_premium: boolean;
  is_promoted: boolean;
  promotion_status: string;
  expires_at: string | null;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  total_listings: number;
  active_listings: number;
  pending_review: number;
  rejected_listings: number;
  sold: number;
  rented: number;
  total_agencies: number;
  total_agents: number;
  reports_open: number;
  listings_created_today: number;
  listings_created_this_week: number;
  [key: string]: number | string | boolean | null;
}

export interface AdminListing {
  id: string;
  reference_code: string;
  cover_image: string | null;
  title: string;
  owner: { id: string | null; name: string; email: string } | null;
  agency: { id: string | null; name: string } | null;
  price: number;
  price_currency: string;
  location: string;
  status: string;
  created_at: string | null;
  views: number;
  reports_count: number;
}

export interface AdminUser {
  id: string;
  email: string;
  phone: string | null;
  full_name: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string | null;
  updated_at: string | null;
  profile: {
    avatar_url: string | null;
    bio: string | null;
    location: string | null;
    preferred_language: string;
    phone_verified: boolean;
    identity_verified: boolean;
  } | null;
}

export interface AdminReport {
  id: string;
  property_id: string;
  reporter_id: string | null;
  reviewer_id: string | null;
  reason: string;
  description: string | null;
  status: string;
  resolution_note: string | null;
  created_at: string | null;
  reviewed_at: string | null;
}

export interface AuditEntry {
  id: string;
  actor: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: Record<string, unknown>;
  created_at: string | null;
  source: "admin_actions" | "moderation";
}

export interface AgencyRow {
  id: string;
  name: string;
  slug: string;
  email: string | null;
  phone: string | null;
  website: string | null;
  logo_url: string | null;
  description: string | null;
  is_verified: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface AgentReputation {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  agency_id: string | null;
  verified_identity: boolean;
  verified_phone: boolean;
  listing_count: number;
  active_listings: number;
  total_views: number;
  reputation_score: number;
}

export interface FeatureRow {
  id: string;
  code: string;
  label_az: string;
  created_at: string | null;
}

export interface ComparableListing {
  id: string;
  title: string;
  reference_code: string;
  price: number | null;
  price_per_m2: number | null;
  rooms: number;
  area_total: number | null;
  status: string;
  city: string | null;
  district: string | null;
  views: number;
  created_at: string | null;
}

export interface PropertyDetail {
  id: string;
  reference_code: string;
  slug: string;
  title: string;
  description: string;
  price: number;
  currency: string;
  deal_type: string;
  property_type: string;
  status: string;
  rooms: number;
  bedrooms: number | null;
  bathrooms: number | null;
  area_total: number;
  area_living: number | null;
  area_land: number | null;
  floor: number | null;
  total_floors: number | null;
  building_type: string | null;
  repair_status: string | null;
  document_type: string | null;
  mortgage_available: boolean;
  furnished: boolean;
  heating: string | null;
  construction_year: number | null;
  is_verified: boolean;
  is_premium: boolean;
  is_promoted: boolean;
  views: number;
  created_at: string;
  seller: AdminUser | null;
  agency: AgencyRow | null;
  reports: AdminReport[];
  moderation_timeline: {
    id: string;
    who: string;
    what: string;
    reason: string;
    timestamp: string;
  }[];
  analytics: { views: number };
  duplicate_signals: {
    id: string;
    reference_code: string;
    title: string;
    price: number | null;
    area_total: number | null;
    rooms: number;
    status: string;
    same_owner: boolean;
    signals: string[];
    confidence: number;
    flag_for_review: boolean;
  }[];
  location?: {
    city: string | null;
    district: string | null;
    neighborhood: string | null;
    metro: string | null;
    address_text: string;
  } | null;
}

function qs(params: Record<string, string | number | boolean | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  }
  const str = search.toString();
  return str ? `?${str}` : "";
}

export const adminApi = {
  async stats(): Promise<AdminStats> {
    return request("/admin/dashboard/stats");
  },

  async listings(params: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
    deal_type?: string;
    property_type?: string;
    city?: string;
    district?: string;
    sort_by?: string;
    sort_order?: string;
  } = {}): Promise<{ data: AdminListing[]; pagination: Pagination }> {
    return request(`/admin/listings${qs({ page: 1, limit: 20, ...params })}`);
  },

  async listingDetail(id: string): Promise<PropertyDetail> {
    return request(`/admin/listings/${id}`);
  },

  async listingAction(
    id: string,
    action:
      | "approve"
      | "reject"
      | "request-edit"
      | "suspend"
      | "archive"
      | "mark-sold"
      | "mark-rented",
    extra: Record<string, unknown> = {}
  ): Promise<unknown> {
    return request(`/admin/listings/${id}/${action}${qs(extra as never)}`, {
      method: "POST"
    });
  },

  async bulkListings(
    action: "bulk-approve" | "bulk-suspend" | "bulk-archive",
    ids: string[]
  ): Promise<unknown> {
    const query = ids.length
      ? `?property_ids=${ids.map((id) => encodeURIComponent(id)).join("&property_ids=")}`
      : "";
    return request(`/admin/listings/${action}${query}`, {
      method: "POST"
    });
  },

  async comparables(id: string): Promise<{
    property_id: string;
    comparable_count: number;
    price_percentile: number | null;
    comparables: ComparableListing[];
    criteria: Record<string, unknown>;
  }> {
    return request(`/admin/listings/${id}/comparables`);
  },

  async users(params: {
    page?: number;
    limit?: number;
    search?: string;
    role?: string;
    is_active?: boolean;
  } = {}): Promise<{ data: AdminUser[]; pagination: Pagination }> {
    return request(`/admin/users${qs({ page: 1, limit: 20, ...params })}`);
  },

  async userUpdate(
    id: string,
    data: {
      full_name?: string;
      role?: string;
      is_active?: boolean;
      is_verified?: boolean;
    }
  ): Promise<AdminUser> {
    return request(`/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data)
    });
  },

  async userDeactivate(id: string): Promise<unknown> {
    return request(`/admin/users/${id}`, { method: "DELETE" });
  },

  async agencies(params: {
    page?: number;
    limit?: number;
    search?: string;
  } = {}): Promise<{ data: AgencyRow[]; pagination: Pagination }> {
    return request(`/admin/agencies${qs({ page: 1, limit: 20, ...params })}`);
  },

  async agencyUpdate(
    id: string,
    data: { name?: string; is_verified?: boolean }
  ): Promise<AgencyRow> {
    return request(`/admin/agencies/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data)
    });
  },

  async agentReputation(params: {
    page?: number;
    limit?: number;
    search?: string;
  } = {}): Promise<{
    data: AgentReputation[];
    pagination: Pagination;
    formula: string;
  }> {
    return request(`/admin/agents/reputation${qs({ page: 1, limit: 20, ...params })}`);
  },

  async reports(params: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
  } = {}): Promise<{ data: AdminReport[]; pagination: Pagination }> {
    return request(`/admin/reports${qs({ page: 1, limit: 20, ...params })}`);
  },

  async reportUpdate(
    id: string,
    data: { status?: string; resolution_note?: string; description?: string }
  ): Promise<AdminReport> {
    return request(`/admin/reports/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data)
    });
  },

  async reportDelete(id: string): Promise<unknown> {
    return request(`/admin/reports/${id}`, { method: "DELETE" });
  },

  async auditLogs(params: {
    page?: number;
    limit?: number;
    action?: string;
    entity_type?: string;
  } = {}): Promise<{
    data: AuditEntry[];
    pagination: Pagination;
    filters: { entity_types: string[] };
  }> {
    return request(`/admin/audit-logs${qs({ page: 1, limit: 50, ...params })}`);
  },

  async marketplaceAnalytics(days = 30): Promise<{
    period_days: number;
    views: number;
    favorites: number;
    phone_reveals: number;
    whatsapp_clicks: number;
    searches: number;
    engagement_rate: number | null;
    listings_by_type: Record<string, number>;
    listings_by_city: { city: string; listings: number }[];
    top_listings: {
      id: string;
      title: string;
      reference_code: string;
      views: number;
    }[];
  }> {
    return request(`/admin/analytics/marketplace${qs({ days })}`);
  },

  async priceIntelligence(params: {
    deal_type?: string;
    property_type?: string;
    city?: string;
    district?: string;
  } = {}): Promise<{
    segments: {
      city: string | null;
      district: string | null;
      count: number;
      avg_price: number;
      median_price: number;
      min_price: number;
      max_price: number;
      avg_price_per_m2: number;
      median_price_per_m2: number;
    }[];
  }> {
    return request(`/admin/price-intelligence${qs(params)}`);
  },

  async features(params: {
    page?: number;
    limit?: number;
    search?: string;
  } = {}): Promise<{
    data: FeatureRow[];
    pagination: Pagination;
    property_types: string[];
  }> {
    return request(`/admin/catalog/features${qs({ page: 1, limit: 100, ...params })}`);
  },

  async featureCreate(data: { code: string; label_az: string }): Promise<FeatureRow> {
    return request("/admin/catalog/features", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  async featureUpdate(id: string, data: { label_az?: string }): Promise<FeatureRow> {
    return request(`/admin/catalog/features/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data)
    });
  },

  async featureDelete(id: string): Promise<unknown> {
    return request(`/admin/catalog/features/${id}`, { method: "DELETE" });
  },

  async locations(): Promise<{
    cities: { name: string; listings: number }[];
    districts: { name: string; listings: number }[];
    metros: { name: string; listings: number }[];
    unlocated: number;
  }> {
    return request("/admin/locations");
  },

  async promotionListing(
    id: string,
    action: "activate" | "deactivate",
    tier?: string,
    days?: number
  ): Promise<unknown> {
    return request(`/admin/promotions/listings/${id}/${action}`, {
      method: "POST",
      body: JSON.stringify({ tier, days })
    });
  },

  async promotedListings(params: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
  } = {}): Promise<{
    data: PromotedListing[];
    pagination: Pagination;
    tiers: Record<string, { label_az: string; days: number }>;
  }> {
    return request(`/admin/promotions/listings${qs({ page: 1, limit: 20, ...params })}`);
  },

  ApiError
};