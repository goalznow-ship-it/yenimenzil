/**
 * Residential complex (new-build development) data access.
 *
 * Demo mode returns an empty list so the UI degrades gracefully without the
 * backend; API mode talks to /complexes.
 */
import type {
  ComplexDetail,
  ResidentialComplex
} from "@yenimenzil/types";
import { API_BASE_URL } from "@/services/api-base";

const API_URL = API_BASE_URL;
export const USE_DEMO_DATA =
  (process.env.NEXT_PUBLIC_USE_DEMO_DATA ?? "true") !== "false";

interface ApiComplex {
  id: string;
  name: string;
  slug: string;
  developer_name: string | null;
  status: string;
  description: string | null;
  address_text: string | null;
  city: string | null;
  district: string | null;
  metro: string | null;
  latitude: number | null;
  longitude: number | null;
  completion_year: number | null;
  total_units: number | null;
  cover_image: string | null;
  amenities: string[];
  is_verified: boolean;
  properties_count: number;
  units_available: number;
  created_at: string;
}

interface ApiComplexDetail extends ApiComplex {
  properties: unknown[];
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API ${response.status} for ${path}`);
  }
  return (await response.json()) as T;
}

function toComplex(api: ApiComplex): ResidentialComplex {
  return {
    id: api.id,
    name: api.name,
    slug: api.slug,
    developerName: api.developer_name ?? undefined,
    status: api.status as ResidentialComplex["status"],
    description: api.description ?? undefined,
    addressText: api.address_text ?? undefined,
    city: api.city ?? undefined,
    district: api.district ?? undefined,
    metro: api.metro ?? undefined,
    latitude: api.latitude ?? undefined,
    longitude: api.longitude ?? undefined,
    completionYear: api.completion_year ?? undefined,
    totalUnits: api.total_units ?? undefined,
    coverImage: api.cover_image ?? undefined,
    amenities: api.amenities ?? [],
    isVerified: api.is_verified,
    propertiesCount: api.properties_count,
    unitsAvailable: api.units_available,
    createdAt: api.created_at
  };
}

export async function fetchComplexes(): Promise<ResidentialComplex[]> {
  if (USE_DEMO_DATA) return [];
  try {
    const body = await fetchJson<ApiComplex[]>("/complexes");
    return body.map(toComplex);
  } catch {
    return [];
  }
}

export async function fetchComplexById(
  id: string
): Promise<ComplexDetail | undefined> {
  if (USE_DEMO_DATA) return undefined;
  try {
    const body = await fetchJson<ApiComplexDetail>(`/complexes/${id}`);
    const base = toComplex(body);
    return { ...base, properties: body.properties as ComplexDetail["properties"] };
  } catch {
    return undefined;
  }
}