import { API_URL } from "@/services/property-api";
import type { PublicBanner } from "@/features/advertising/ad-rail";

export async function fetchPublicBanners(): Promise<PublicBanner[]> {
  try { const response = await fetch(`${API_URL}/public/platform/banners`, { cache: "no-store" }); return response.ok ? response.json() : []; } catch { return []; }
}
