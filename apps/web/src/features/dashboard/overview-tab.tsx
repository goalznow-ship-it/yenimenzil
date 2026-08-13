"use client";

import * as React from "react";
import Link from "next/link";
import { Skeleton } from "@yenimenzil/ui";
import { Eye, Heart, Bell, Building2, TrendingUp } from "lucide-react";
import { dashboardApi, type DashboardSummary } from "@/services/dashboard-api";
import { formatPriceShort } from "@/lib/format";

const STATUS_LABELS: Record<string, string> = {
  active: "Aktiv",
  inactive: "Deaktiv",
  pending: "Gözləmədə",
  rejected: "Rədd edilib",
  archived: "Arxivləşib"
};

export function OverviewTab() {
  const [summary, setSummary] = React.useState<DashboardSummary | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    dashboardApi
      .summary()
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : "Xəta"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28 rounded-2xl" />
        ))}
      </div>
    );
  }

  const statusCounts = summary?.property_status_counts ?? {};
  const totalListings = Object.values(statusCounts).reduce((a, b) => a + b, 0);
  const totalViews = summary?.total_views ?? 0;
  const totalFavorites = summary?.total_favorites ?? 0;
  const unreadNotifications = summary?.unread_notifications ?? 0;

  const stats = [
    {
      label: "Ümumi elanlar",
      value: String(totalListings),
      icon: Building2,
      href: null
    },
    {
      label: "Baxışlar",
      value: formatPriceShort(totalViews),
      icon: Eye,
      href: null
    },
    {
      label: "Seçilmişlər",
      value: formatPriceShort(totalFavorites),
      icon: Heart,
      href: null
    },
    {
      label: "Oxunmamış bildiriş",
      value: String(unreadNotifications),
      icon: Bell,
      href: unreadNotifications > 0 ? "/profile?tab=notifications" : null
    }
  ];

  return (
    <div className="space-y-6">
      {error ? (
        <p className="rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">
          {error}
        </p>
      ) : null}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((stat) => (
          <Link
            key={stat.label}
            href={stat.href ?? "#"}
            aria-disabled={!stat.href}
            className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70 transition-shadow hover:shadow-md"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-soft text-brand">
              <stat.icon className="h-4.5 w-4.5" />
            </div>
            <p className="mt-3 text-2xl font-semibold tabular-nums tracking-tight">
              {stat.value}
            </p>
            <p className="mt-0.5 text-[13px] text-muted-foreground">{stat.label}</p>
          </Link>
        ))}
      </div>

      {totalListings > 0 ? (
        <div className="rounded-2xl bg-surface p-5 ring-1 ring-border/70">
          <h2 className="flex items-center gap-2 text-[15px] font-semibold">
            <TrendingUp className="h-4 w-4 text-brand" />
            Elanların statusu üzrə paylanması
          </h2>
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {Object.entries(statusCounts).map(([status, count]) => (
              <div
                key={status}
                className="rounded-xl bg-foreground/[0.03] px-4 py-3 ring-1 ring-border/60"
              >
                <p className="text-lg font-semibold tabular-nums">{count}</p>
                <p className="text-xs text-muted-foreground">
                  {STATUS_LABELS[status] ?? status}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-border bg-surface p-10 text-center">
          <p className="text-sm text-muted-foreground">
            Hələ elanınız yoxdur. İlk elanınızı yerləşdirin.
          </p>
          <Link
            href="/add-property"
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand/90"
          >
            <Building2 className="h-4 w-4" />
            Elan yerləşdir
          </Link>
        </div>
      )}
    </div>
  );
}
