import { API_URL } from "@/services/property-api";

export interface DirectoryAgency { id: string; name: string; slug: string; logo_url?: string | null; description?: string | null; is_verified: boolean; }

export async function fetchAgencyDirectory(limit = 8): Promise<DirectoryAgency[]> {
  try { const response = await fetch(`${API_URL}/agencies?limit=${limit}`, { cache: "no-store" }); return response.ok ? response.json() : []; } catch { return []; }
}
