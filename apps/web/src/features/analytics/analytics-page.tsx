"use client";

import * as React from "react";
import Link from "next/link";
import { Skeleton, Badge } from "@yenimenzil/ui";
import {
  Eye,
  Heart,
  Phone,
  MessageSquare,
  TrendingUp,
  Building2
} from "lucide-react";
import { dashboardApi, type MyPropertySummary } from "@/services/dashboard-api";
import { formatPriceShort } from "@/lib/format";
import { RequireAuth } from "@/components/auth/auth-provider";
import { useAuth } from "@/store/auth";

interface ListingAnalytics {
  property_id: string;
  views: number;
  favorites: number;
  phone_reveals: number;
  whatsapp_clicks: number;
  messages: number;
  viewing_requests: number;
  days: number;
  period_views: number;
  trend: {
    date: string;
    views: number;
    favorites: number;
    phone_reveals: number;
    whatsapp_clicks: number;
    messages: number;
  }[];
  conversion: {
    favorite_rate: number;
    phone_rate: number;
    whatsapp_rate: number;
    message_rate: number;
    viewing_request_rate: number;
  };
}

interface AgencyAnalytics {
  agency_id: string | null;
  agency_name: string;
  days: number;
  listings_count: number;
  total_views: number;
  total_favorites: number;
  total_leads: number;
  avg_price: number;
  top_listings: {
    property_id: string;
    title: string;
    views: number;
    favorites: number;
    phone_reveals: number;
    messages: number;
  }[];
}

export function AnalyticsPage() {
  const [listings, setListings] = React.useState<MyPropertySummary[]>([]);
  const [analytics, setAnalytics] = React.useState<Record<string, ListingAnalytics>>({});
  const [summary, setSummary] = React.useState<{
    total_views: number;
    total_favorites: number;
    property_status_counts: Record<string, number>;
  } | null>(null);
  const [agency, setAgency] = React.useState<AgencyAnalytics | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const user = useAuth((s) => s.user);

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
        const agencyData = await dashboardApi.agencyAnalytics();
        if (cancelled) return;
        setAgency(agencyData);
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

  const periodViews = Object.values(analytics).reduce(
    (acc, a) => acc + a.period_views,
    0
  );
  const conversionCards = [
    {
      label: "Baxış → Seçilmiş",
      value: (() => {
        const favorites = Object.values(analytics).reduce(
          (acc, a) => acc + a.favorites,
          0
        );
        return periodViews > 0 ? ((favorites * 100) / periodViews).toFixed(1) : "0";
      })() + "%"
    },
    {
      label: "Baxış → Telefon",
      value: (() => {
        const reveals = Object.values(analytics).reduce(
          (acc, a) => acc + a.phone_reveals,
          0
        );
        return periodViews > 0 ? ((reveals * 100) / periodViews).toFixed(1) : "0";
      })() + "%"
    },
    {
      label: "Baxış → Mesaj",
      value: (() => {
        const messages = Object.values(analytics).reduce(
          (acc, a) => acc + a.messages,
          0
        );
        return periodViews > 0 ? ((messages * 100) / periodViews).toFixed(1) : "0";
      })() + "%"
    },
    {
      label: "Baxış → WhatsApp",
      value: (() => {
        const clicks = Object.values(analytics).reduce(
          (acc, a) => acc + a.whatsapp_clicks,
          0
        );
        return periodViews > 0 ? ((clicks * 100) / periodViews).toFixed(1) : "0";
      })() + "%"
    }
  ];

  const trendByDate = new Map<string, number>();
  for (const a of Object.values(analytics)) {
    for (const point of a.trend) {
      trendByDate.set(point.date, (trendByDate.get(point.date) ?? 0) + point.views);
    }
  }
  const trendDates = Array.from(trendByDate.keys());
  const maxTrend = Math.max(1, ...trendByDate.values());
  const isAgencyMember =
    user?.role === "agent" || user?.role === "agency_admin";

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
              Konversiya (son 30 gün)
            </h2>
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              {conversionCards.map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-2xl bg-surface p-4 ring-1 ring-border/70"
                >
                  <p className="text-xl font-semibold tabular-nums tracking-tight">
                    {stat.value}
                  </p>
                  <p className="mt-0.5 text-[13px] text-muted-foreground">{stat.label}</p>
                </div>
              ))}
            </div>

            {trendDates.length > 0 ? (
              <div className="mt-6 rounded-2xl bg-surface p-5 ring-1 ring-border/70">
                <p className="mb-4 text-[13px] font-medium text-muted-foreground">
                  Gündəlik baxış tendensiyası
                </p>
                <div className="flex h-32 items-end gap-1">
                  {trendDates.map((date) => {
                    const value = trendByDate.get(date) ?? 0;
                    const height = Math.max(4, Math.round((value / maxTrend) * 100));
                    return (
                      <div key={date} className="group relative flex-1">
                        <div
                          className="w-full rounded-t bg-brand/70 transition-colors group-hover:bg-brand"
                          style={{ height: `${height}%` }}
                        />
                        <div className="pointer-events-none absolute -top-8 left-1/2 z-10 -translate-x-1/2 whitespace-nowrap rounded-md bg-foreground px-2 py-1 text-[11px] text-background opacity-0 transition-opacity group-hover:opacity-100">
                          {date}: {value}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : null}

            {isAgencyMember && agency && agency.listings_count > 0 ? (
              <div className="mt-8 rounded-2xl bg-surface p-5 ring-1 ring-border/70">
                <div className="flex items-center justify-between gap-2">
                  <h2 className="flex items-center gap-2 text-[15px] font-semibold">
                    <Building2 className="h-4 w-4 text-brand" />
                    Agentlik portfeli — {agency.agency_name || "Agentlik"}
                  </h2>
                  <span className="text-xs text-muted-foreground">
                    {agency.listings_count} elan · {formatPriceShort(agency.total_views)} baxış ·{" "}
                    {agency.total_leads} lead
                  </span>
                </div>
                <div className="mt-3 overflow-x-auto">
                  <table className="w-full min-w-[520px] text-sm">
                    <thead>
                      <tr className="border-b border-border/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
                        <th className="p-2.5 font-medium">Elan</th>
                        <th className="p-2.5 text-right font-medium">Baxış</th>
                        <th className="p-2.5 text-right font-medium">Seçilmiş</th>
                        <th className="p-2.5 text-right font-medium">Telefon</th>
                        <th className="p-2.5 text-right font-medium">Mesaj</th>
                      </tr>
                    </thead>
                    <tbody>
                      {agency.top_listings.map((listing) => (
                        <tr key={listing.property_id} className="border-b border-border/50 last:border-0">
                          <td className="max-w-[300px] p-2.5">
                            <Link
                              href={`/property/${listing.property_id}`}
                              className="line-clamp-1 font-medium text-foreground transition-colors hover:text-brand"
                            >
                              {listing.title}
                            </Link>
                          </td>
                          <td className="p-2.5 text-right tabular-nums">{listing.views}</td>
                          <td className="p-2.5 text-right tabular-nums">{listing.favorites}</td>
                          <td className="p-2.5 text-right tabular-nums">{listing.phone_reveals}</td>
                          <td className="p-2.5 text-right tabular-nums">{listing.messages}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}

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
