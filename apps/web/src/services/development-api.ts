import { API_URL } from "@/services/property-api";

export interface Developer {
  id: string; name: string; slug: string; description?: string | null;
  logo_url?: string | null; phone?: string | null; website?: string | null; is_verified: boolean;
}
export interface ComplexUnitType {
  id: string; rooms: number; area_from: number; area_to?: number | null;
  price_from?: number | null; available_count: number; plan_url?: string | null;
}
export interface ResidentialComplex {
  id: string; name: string; slug: string; description?: string | null;
  city: string; district?: string | null; address: string;
  delivery_date?: string | null; delivery_status: string;
  min_price?: number | null; price_per_sqm_from?: number | null; currency: string;
  cover_url?: string | null; gallery: string[]; amenities: string[];
  payment_terms?: string | null; buildings_count?: number | null;
  is_featured: boolean; developer: Developer; unit_types: ComplexUnitType[];
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Development API error: ${response.status}`);
  return response.json() as Promise<T>;
}

export function fetchComplexes(query = "") {
  const suffix = query ? `?q=${encodeURIComponent(query)}` : "";
  return getJson<ResidentialComplex[]>(`/developments/complexes${suffix}`);
}

export function fetchComplex(slug: string) {
  return getJson<ResidentialComplex>(`/developments/complexes/${encodeURIComponent(slug)}`);
}
