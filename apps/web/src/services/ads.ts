/**
 * Advertising service (Phase 15).
 *
 * Batch-fetches ads for all placements on a page, caches them in-memory,
 * and provides impression/click tracking.
 */
import type { AdCampaignPublic, AdPlacement } from "@yenimenzil/types";
import { API_BASE_URL } from "@/services/api-base";

const API_URL = API_BASE_URL;
export const USE_DEMO_DATA =
  (process.env.NEXT_PUBLIC_USE_DEMO_DATA ?? "true") !== "false";

interface AdCacheEntry {
  ads: AdCampaignPublic[];
  fetchedAt: number;
}

const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes
const adCache = new Map<AdPlacement, AdCacheEntry>();

function isCacheValid(entry: AdCacheEntry): boolean {
  return Date.now() - entry.fetchedAt < CACHE_TTL_MS;
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`API ${response.status} for ${path}`);
  }
  return (await response.json()) as T;
}

/** Fetch ads for a single placement. */
export async function fetchAdsForPlacement(
  placement: AdPlacement,
  options: { device?: "desktop" | "mobile"; city?: string; category?: string } = {}
): Promise<AdCampaignPublic | null> {
  const cacheKey = `${placement}-${options.device}-${options.city ?? ""}-${options.category ?? ""}`;
  const cached = adCache.get(cacheKey as AdPlacement);
  if (cached && isCacheValid(cached)) {
    return cached.ads[0] ?? null;
  }

  if (USE_DEMO_DATA) return null;

  try {
    const params = new URLSearchParams();
    params.set("placement", placement);
    if (options.device) params.set("device", options.device);
    if (options.city) params.set("city", options.city);
    if (options.category) params.set("category", options.category);

    const ads = await fetchJson<AdCampaignPublic[]>(`/ads?${params.toString()}`);
    adCache.set(cacheKey as AdPlacement, { ads, fetchedAt: Date.now() });
    return ads[0] ?? null;
  } catch {
    return null;
  }
}

/** Batch fetch ads for multiple placements. */
export async function fetchAdsForPlacements(
  placements: AdPlacement[],
  options: { device?: "desktop" | "mobile"; city?: string; category?: string } = {}
): Promise<Record<AdPlacement, AdCampaignPublic | null>> {
  if (USE_DEMO_DATA) {
    return Object.fromEntries(placements.map((p) => [p, null])) as Record<
      AdPlacement,
      AdCampaignPublic | null
    >;
  }

  try {
    const params = new URLSearchParams();
    params.set("placements", placements.join(","));
    if (options.device) params.set("device", options.device);
    if (options.city) params.set("city", options.city);
    if (options.category) params.set("category", options.category);

    const ads = await fetchJson<AdCampaignPublic[]>(`/ads?${params.toString()}`);
    const byPlacement = new Map<string, AdCampaignPublic | null>();
    for (const ad of ads) {
      byPlacement.set(ad.placement, ad);
    }
    for (const p of placements) {
      byPlacement.set(p, byPlacement.get(p) ?? null);
    }
    return Object.fromEntries(byPlacement) as Record<
      AdPlacement,
      AdCampaignPublic | null
    >;
  } catch {
    return Object.fromEntries(placements.map((p) => [p, null])) as Record<
      AdPlacement,
      AdCampaignPublic | null
    >;
  }
}

/** Record an ad impression (deduplicated on server). */
export async function recordImpression(
  campaignId: string,
  sessionKey?: string
): Promise<void> {
  if (USE_DEMO_DATA) return;
  try {
    await fetch(`${API_URL}/ads/${campaignId}/impression`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ session_key: sessionKey }),
    });
  } catch {
    // swallow - analytics failure must not break rendering
  }
}

/** Record an ad click (deduplicated on server). */
export async function recordClick(
  campaignId: string,
  sessionKey?: string
): Promise<void> {
  if (USE_DEMO_DATA) return;
  try {
    await fetch(`${API_URL}/ads/${campaignId}/click`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ session_key: sessionKey }),
    });
  } catch {
    // swallow
  }
}

/** Generate a simple session key for dedup (stored in sessionStorage). */
export function getAdSessionKey(): string {
  if (typeof window === "undefined") return "";
  let key = sessionStorage.getItem("yenimenzil_ad_session");
  if (!key) {
    key = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    sessionStorage.setItem("yenimenzil_ad_session", key);
  }
  return key;
}

/** Check if placement is desktop-only. */
export function isDesktopPlacement(placement: AdPlacement): boolean {
  return !placement.startsWith("MOBILE_");
}

/** Check if placement is mobile-only. */
export function isMobilePlacement(placement: AdPlacement): boolean {
  return placement.startsWith("MOBILE_");
}

/** Get placement display label for admin UI. */
export function placementLabel(placement: AdPlacement): string {
  switch (placement) {
    case "LEFT_RAIL":
      return "Sol Rail (Masaüstü)";
    case "RIGHT_RAIL":
      return "Sağ Rail (Masaüstü)";
    case "HOME_TOP_BANNER":
      return "Ana Səhifə - Üst Banner";
    case "HOME_MIDDLE_BANNER":
      return "Ana Səhifə - Orta Banner";
    case "SEARCH_TOP_BANNER":
      return "Axtarış - Üst Banner";
    case "SEARCH_INLINE_BANNER":
      return "Axtarış - İnlayn Banner";
    case "SEARCH_BOTTOM_BANNER":
      return "Axtarış - Alt Banner";
    case "PROPERTY_SIDE_AD":
      return "Elan - Yan Reklam";
    case "PROPERTY_INLINE_AD":
      return "Elan - İnlayn Reklam";
    case "MOBILE_TOP":
      return "Mobil - Üst";
    case "MOBILE_INLINE":
      return "Mobil - İnlayn";
    case "MOBILE_BOTTOM":
      return "Mobil - Alt";
    default:
      return placement;
  }
}