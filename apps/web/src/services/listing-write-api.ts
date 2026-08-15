/**
 * Authenticated write operations for listings (create/update/submit/delete).
 * These always talk to the FastAPI backend with cookies.
 */

export interface ListingLocationInput {
  latitude: number;
  longitude: number;
  address_text: string;
  city: string;
  district?: string;
  settlement?: string;
  neighborhood?: string;
  metro?: string;
}

export interface ListingInput {
  title: string;
  description: string;
  deal_type: "sale" | "rent" | "daily";
  property_type: string;
  price: number;
  currency: "AZN" | "USD" | "EUR";
  rooms: number;
  bedrooms?: number;
  bathrooms?: number;
  area_total: number;
  area_living?: number;
  floor?: number;
  total_floors?: number;
  building_type?: "new" | "old";
  repair_status?: string;
  document_type?: string;
  mortgage_available: boolean;
  furnished?: boolean;
  heating?: string;
  construction_year?: number;
  location: ListingLocationInput;
  features: string[];
  media: { url: string; alt?: string; is_cover?: boolean }[];
}

import { API_BASE_URL } from "@/services/api-base";

const BASE = API_BASE_URL;

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
      (body && typeof body.detail === "string" && body.detail) || "Xəta baş verdi";
    throw new Error(detail);
  }
  return body as T;
}

export interface ListingWriteResult {
  id: string;
  status: string;
  reference_code?: string;
  published_at?: string | null;
}

export interface ListingDetail extends ListingWriteResult {
  title: string;
  description?: string;
  deal_type: "sale" | "rent" | "daily";
  property_type: string;
  price: number;
  currency: "AZN" | "USD" | "EUR";
  rooms: number;
  bedrooms?: number | null;
  bathrooms?: number | null;
  area_total: number;
  floor?: number | null;
  total_floors?: number | null;
  building_type?: "new" | "old" | null;
  repair_status?: string | null;
  document_type?: string | null;
  mortgage_available: boolean;
  features: string[];
  location?: {
    city: string | null;
    district: string | null;
    metro: string | null;
    address_text: string | null;
  } | null;
  media?: { url: string }[];
}

export const listingWriteApi = {
  async get(id: string): Promise<ListingDetail> {
    return request(`/properties/${id}`);
  },

  async create(input: ListingInput): Promise<ListingWriteResult> {
    return request("/properties", { method: "POST", body: JSON.stringify(input) });
  },

  async update(
    id: string,
    patch: Partial<ListingInput> & { status?: string }
  ): Promise<ListingWriteResult> {
    return request(`/properties/${id}`, {
      method: "PATCH",
      body: JSON.stringify(patch)
    });
  },

  async submit(id: string): Promise<ListingWriteResult> {
    return request(`/properties/${id}/submit`, { method: "POST" });
  },

  async remove(id: string): Promise<void> {
    return request(`/properties/${id}`, { method: "DELETE" });
  },

  async mine(status?: string): Promise<ListingWriteResult[]> {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return request(`/properties/mine${qs}`);
  }
};
