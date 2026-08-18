export const appConfig = {
  name: "IdealEv",
  domain: "idealev.az",
  slogan: "IdealEvda elan bul.",
  primaryColor: "#15543F",
  features: {
    priceIntelligence: true,
    trustScore: false
  }
} as const;

export const siteUrl =
  process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

export const apiUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const useDemoData = process.env.NEXT_PUBLIC_USE_DEMO_DATA !== "false";

export const mapTilesUrl =
  process.env.NEXT_PUBLIC_MAP_TILES_URL ??
  "https://tile.openstreetmap.org/{z}/{x}/{y}.png";

export const demoMapCenter = { lat: 40.4093, lng: 49.8671 };
