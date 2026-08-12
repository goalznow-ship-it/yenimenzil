"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { adminApi } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";

interface MarketplaceAnalytics {
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
}

export default function AdminAnalyticsPage() {
  const [data, setData] = React.useState<MarketplaceAnalytics | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminApi.marketplaceAnalytics();
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xəta");
    } finally {
      setLoading(false);
    }
  }, []);

   React.useEffect(() => {
     // eslint-disable-next-line react-hooks/set-state-in-effect
     load();
     // eslint-disable-next-line react-hooks/exhaustive-deps
   }, []);

  if (error) {
    return (
      <div>
        <AdminPageHeader title="Marketplace analitikası" subtitle="Ümumi marketplace statistikaları" icon={Search} />
        <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div>
        <AdminPageHeader title="Marketplace analitikası" subtitle="Ümumi marketplace statistikaları" icon={Search} />
        <div className="space-y-6">
          <div className="h-20 animate-pulse rounded-2xl bg-foreground/[0.04]" />
          <div className="h-20 animate-pulse rounded-2xl bg-foreground/[0.04]" />
          <div className="h-20 animate-pulse rounded-2xl bg-foreground/[0.04]" />
          <div className="h-20 animate-pulse rounded-2xl bg-foreground/[0.04]" />
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div>
        <AdminPageHeader title="Marketplace analitikası" subtitle="Ümumi marketplace statistikaları" icon={Search} />
        <p className="text-center text-foreground/50">Heç bir məlumat yoxdur</p>
      </div>
    );
  }

  return (
    <div>
      <AdminPageHeader title="Marketplace analitikası" subtitle="Ümumi marketplace statistikaları" icon={Search} />
      <div className="space-y-6">
        <div className="rounded-2xl border border-border/60 bg-surface p-4">
          <h2 className="mb-3 font-semibold">Ümumi baxışlar</h2>
          <p className="text-2xl font-semibold">{data.views?.toLocaleString() ?? "0"}</p>
        </div>

        <div className="rounded-2xl border border-border/60 bg-surface p-4">
          <h2 className="mb-3 font-semibold">Məxfəllər</h2>
          <p className="text-2xl font-semibold">{data.favorites?.toLocaleString() ?? "0"}</p>
        </div>

        <div className="rounded-2xl border border-border/60 bg-surface p-4">
          <h2 className="mb-3 font-semibold">Telefon nömrəsi göstərilməsi</h2>
          <p className="text-2xl font-semibold">{data.phone_reveals?.toLocaleString() ?? "0"}</p>
        </div>

        <div className="rounded-2xl border border-border/60 bg-surface p-4">
          <h2 className="mb-3 font-semibold">WhatsApp klikləri</h2>
          <p className="text-2xl font-semibold">{data.whatsapp_clicks?.toLocaleString() ?? "0"}</p>
        </div>

        <div className="rounded-2xl border border-border/60 bg-surface p-4">
          <h2 className="mb-3 font-semibold">Axtarışlar</h2>
          <p className="text-2xl font-semibold">{data.searches?.toLocaleString() ?? "0"}</p>
        </div>

        {data.engagement_rate !== null && (
          <div className="rounded-2xl border border-border/60 bg-surface p-4">
            <h2 className="mb-3 font-semibold">Engagement tauxı</h2>
            <p className="text-2xl font-semibold">{data.engagement_rate.toFixed(2)}</p>
          </div>
        )}

        <div className="rounded-2xl border border-border/60 bg-surface p-4">
          <h2 className="mb-3 font-semibold">Tip üzrə elanlar</h2>
          {data.listings_by_type ? (
            <div className="space-y-2">
               {Object.entries(data.listings_by_type).map(([type, count]: [string, number]) => (
                <div key={type} className="flex items-center justify-between rounded-xl border border-border/50 p-3">
                  <span>{type}</span>
                  <span className="font-medium">{count} elan</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-foreground/50">Məlumat yoxdur</p>
          )}
        </div>

        <div className="rounded-2xl border border-border/60 bg-surface p-4">
          <h2 className="mb-3 font-semibold">Şəhər üzrə elanlar</h2>
          {data.listings_by_city ? (
            <div className="space-y-2">
               {data.listings_by_city.map((city: { city: string; listings: number }) => (
                <div key={city.city} className="flex items-center justify-between rounded-xl border border-border/50 p-3">
                  <span>{city.city}</span>
                  <span className="font-medium">{city.listings} elan</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-foreground/50">Məlumat yoxdur</p>
          )}
        </div>

        <div className="rounded-2xl border border-border/60 bg-surface p-4">
          <h2 className="mb-3 font-semibold">Top 10 görünən elanlar</h2>
          {data.top_listings ? (
            <div className="space-y-2">
               {data.top_listings.map((listing: { id: string; title: string; reference_code: string; views: number }) => (
                <div key={listing.id} className="flex items-center justify-between rounded-xl border border-border/50 p-3">
                  <div>
                    <span className="font-medium">{listing.title}</span>
                    <p className="text-xs text-foreground/50">{listing.reference_code}</p>
                  </div>
                  <span className="font-medium">{listing.views} baxış</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-foreground/50">Məlumat yoxdur</p>
          )}
        </div>
      </div>
    </div>
  );
}