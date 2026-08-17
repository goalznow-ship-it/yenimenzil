import * as React from "react";
import type { AdPlacement, AdCampaignPublic } from "@yenimenzil/types";
import {
  fetchAdsForPlacements,
} from "@/services/ads";

interface AdsContextValue {
  ads: Record<AdPlacement, AdCampaignPublic | null>;
  loading: boolean;
  refresh: () => Promise<void>;
}

const AdsContext = React.createContext<AdsContextValue | null>(null);

interface AdsProviderProps {
  children: React.ReactNode;
  placements: AdPlacement[];
  device?: "desktop" | "mobile";
  city?: string;
  category?: string;
}

export function AdsProvider({
  children,
  placements,
  device = "desktop",
  city,
  category,
}: AdsProviderProps) {
  const [ads, setAds] = React.useState<Record<AdPlacement, AdCampaignPublic | null>>(
    Object.fromEntries(placements.map((p) => [p, null])) as Record<
      AdPlacement,
      AdCampaignPublic | null
    >
  );
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      if (placements.length === 0) {
        setAds(Object.fromEntries(placements.map((p) => [p, null])) as Record<AdPlacement, AdCampaignPublic | null>);
        return;
      }
      const fetched = await fetchAdsForPlacements(placements, {
        device,
        city,
        category,
      });
      setAds(fetched);
    } finally {
      setLoading(false);
    }
  }, [placements, device, city, category]);

  React.useEffect(() => {
    void Promise.resolve().then(() => load());
  }, [load]);

  return (
    <AdsContext.Provider value={{ ads, loading, refresh: load }}>
      {children}
    </AdsContext.Provider>
  );
}

export function useAds() {
  const ctx = React.useContext(AdsContext);
  if (!ctx) {
    throw new Error("useAds must be used within AdsProvider");
  }
  return ctx;
}

/** Hook to get a specific ad by placement. */
export function useAd(placement: AdPlacement) {
  const { ads } = useAds();
  return ads[placement] ?? null;
}