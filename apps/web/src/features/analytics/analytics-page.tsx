"use client";

import * as React from "react";
import Link from "next/link";
import { Skeleton, Badge } from "@yenimenzil/ui";
import { Eye, Heart, Phone, MessageSquare, TrendingUp } from "lucide-react";
import { dashboardApi, type MyPropertySummary } from "@/services/dashboard-api";
import { formatPriceShort } from "@/lib/format";
import { RequireAuth } from "@/components/auth/auth-provider";

interface ListingAnalytics {
  property_id: string;
  views: number;
  favorites: number;
  phone_reveals: number;
  whatsapp_clicks: number;
  messages: number;
  viewing_requests: number;
}

export function AnalyticsPage() {
  const [listings, setListings] = React.useState<MyPropertySummary[]>([]);
  const [analytics, setAnalytics] = React.useState<Record<string, ListingAnalytics>>({});
  const [summary, setSummary] = React.useState<{
    total_views: number;
    total_favorites: number;
    property_status_counts: Record<string, number>;
  } | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    Promise.all([dashboardApi.myProperties(), dashboardApi.summary()])
      .then(async ([mine, sum]) => {
        if (cancelled) return;
        setListings(mine);
        setSummary(sum);
        const entries = await Promise.all(
          mine.map(async (listing) => {
            try {
              const analytics = await dashboardApi.listingAnalytics(listing.id);
              return [listing.id, analytics] as const;
            } catch {
              return null;
            }
          })
        );
        if (cancelled) return;
        const map: Record<string, ListingAnalytics> = {};
        for (const entry of entries) {
          if (entry) map[entry[0]] = entry[1];
        }
        setAnalytics(map);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Xəta");
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const STATUS_LABELS: Record<string, string> = {
    active: "Aktiv",
    inactive: "Deaktiv",
    pending: "Gözləmədə",
    rejected: "Rədd edilib",
    archived: "Arxivləşib"
  };

  const totalViews = summary?.total_views ?? 0;
  const totalFavorites = summary?.total_favorites ?? 0;
  const totalReveals = Object.values(analytics).reduce(
    (acc, a) => acc + a.phone_reveals + a.whatsapp_clicks,
    0
  );
  const totalMessages = Object.values(analytics).reduce(
    (acc, a) => acc + a.messages + a.viewing_requests,
    0
  );

  const statCards = [
    { label: "Ümumi baxış", value: formatPriceShort(totalViews), icon: Eye },
    { label: "Ümumi seçilmiş", value: formatPriceShort(totalFavorites), icon: Heart },
    { label: "Telefon + WhatsApp", value: formatPriceShort(totalReveals), icon: Phone },
    { label: "Mesaj + baxış təklifi", value: formatPriceShort(totalMessages), icon: MessageSquare }
  ];

  return (
    <RequireAuth>
      <div className="mx-auto w-full max-w-5xl px-4 py-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Satış statistikası</h1>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Elanlarınızın görünürlük və maraqlanma göstəriciləri.
            </p>
          </div>
          <Link
            href="/profile"
            className="text-[13px] font-medium text-muted-foreground transition-colors hover:text-brand"
          >
            ← İdarə paneli
          </Link>
        </div>

        {error ? (
          <p className="mt-6 rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">
            {error}
          </p>
        ) : null}

        {loading ? (
          <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-28 rounded-2xl" />
            ))}
            <div className="col-span-full space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-20 rounded-2xl" />
              ))}
            </div>
          </div>
        ) : (
          <>
            <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
              {statCards.map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70"
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-soft text-brand">
                    <stat.icon className="h-4.5 w-4.5" />
                  </div>
                  <p className="mt-3 text-2xl font-semibold tabular-nums tracking-tight">
                    {stat.value}
                  </p>
                  <p className="mt-0.5 text-[13px] text-muted-foreground">{stat.label}</p>
                </div>
              ))}
            </div>

            <h2 className="mt-8 mb-3 flex items-center gap-2 text-[15px] font-semibold">
              <TrendingUp className="h-4 w-4 text-brand" />
              Elanlar üzrə ətraflı göstəricilər
            </h2>

            {listings.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-border bg-surface p-10 text-center">
                <p className="text-sm text-muted-foreground">
                  Hələ elanınız yoxdur. Elan yerləşdirdikdən sonra statistika burada
                  görünəcək.
                </p>
                <Link
                  href="/add-property"
                  className="mt-4 inline-flex rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand/90"
                >
                  Elan yerləşdir
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto rounded-2xl bg-surface ring-1 ring-border/70">
                <table className="w-full min-w-[640px] text-sm">
                  <thead>
                    <tr className="border-b border-border/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
                      <th className="p-3 font-medium">Elan</th>
                      <th className="p-3 font-medium">Status</th>
                      <th className="p-3 text-right font-medium">Baxış</th>
                      <th className="p-3 text-right font-medium">Seçilmiş</th>
                      <th className="p-3 text-right font-medium">Telefon</th>
                      <th className="p-3 text-right font-medium">Mesaj</th>
                    </tr>
                  </thead>
                  <tbody>
                    {listings.map((listing) => {
                      const a = analytics[listing.id];
                      return (
                        <tr key={listing.id} className="border-b border-border/50 last:border-0">
                          <td className="max-w-[280px] p-3">
                            <Link
                              href={`/property/${listing.id}`}
                              className="line-clamp-1 font-medium text-foreground transition-colors hover:text-brand"
                            >
                              {listing.title}
                            </Link>
                            <p className="text-xs text-muted-foreground">
                              {listing.id.slice(0, 8)}
                            </p>
                          </td>
                          <td className="p-3">
                            <Badge
                              variant={
                                listing.status === "active"
                                  ? "green"
                                  : listing.status === "pending"
                                    ? "amber"
                                    : listing.status === "rejected"
                                      ? "red"
                                      : "neutral"
                              }
                            >
                              {STATUS_LABELS[listing.status] ?? listing.status}
                            </Badge>
                          </td>
                          <td className="p-3 text-right tabular-nums">
                            {a?.views ?? listing.views}
                          </td>
                          <td className="p-3 text-right tabular-nums">
                            {a?.favorites ?? 0}
                          </td>
                          <td className="p-3 text-right tabular-nums">
                            {(a?.phone_reveals ?? 0) + (a?.whatsapp_clicks ?? 0)}
                          </td>
                          <td className="p-3 text-right tabular-nums">
                            {(a?.messages ?? 0) + (a?.viewing_requests ?? 0)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </RequireAuth>
  );
}
