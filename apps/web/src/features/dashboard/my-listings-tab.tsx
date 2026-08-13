"use client";

import * as React from "react";
import Link from "next/link";
import { Skeleton, Badge, EmptyState } from "@yenimenzil/ui";
import { Building2, Eye, Trash2, PauseCircle, PlayCircle, Star } from "lucide-react";
import { dashboardApi, type MyPropertySummary } from "@/services/dashboard-api";
import { formatPrice, formatDate } from "@/lib/format";

const STATUS_BADGE: Record<string, React.ComponentProps<typeof Badge>["variant"]> = {
  active: "green",
  inactive: "neutral",
  pending: "amber",
  rejected: "red",
  archived: "neutral"
};

const STATUS_LABELS: Record<string, string> = {
  active: "Aktiv",
  inactive: "Deaktiv",
  pending: "Gözləmədə",
  rejected: "Rədd edilib",
  archived: "Arxivləşib"
};

export function MyListingsTab() {
  const [listings, setListings] = React.useState<MyPropertySummary[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busyId, setBusyId] = React.useState<string | null>(null);

  const load = React.useCallback(() => {
    dashboardApi
      .myProperties()
      .then((data) => {
        setListings(data);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Xəta"));
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  const toggleStatus = async (listing: MyPropertySummary) => {
    if (!listings) return;
    setBusyId(listing.id);
    setError(null);
    try {
      const next = listing.status === "active" ? "inactive" : "active";
      await dashboardApi.togglePropertyStatus(listing.id, next);
      setListings(
        listings.map((l) => (l.id === listing.id ? { ...l, status: next } : l))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (id: string) => {
    if (!window.confirm("Elanı silmək istədiyinizə əminsiniz?")) return;
    if (!listings) return;
    setBusyId(id);
    setError(null);
    try {
      await dashboardApi.deleteProperty(id);
      setListings(listings.filter((l) => l.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setBusyId(null);
    }
  };

  if (!listings && !error) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex gap-4 rounded-2xl bg-surface p-3 ring-1 ring-border/70">
            <Skeleton className="h-32 w-40 rounded-xl" />
            <div className="flex-1 space-y-2.5 py-1">
              <Skeleton className="h-5 w-1/3" />
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-3.5 w-1/3" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return <p className="rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">{error}</p>;
  }

  if (!listings || listings.length === 0) {
    return (
      <EmptyState
        icon={<Building2 className="h-7 w-7" />}
        title="Elanınız yoxdur"
        description="Yerləşdirdiyiniz elanlar burada görünəcək."
        action={
          <Link
            href="/add-property"
            className="inline-flex items-center gap-2 rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand/90"
          >
            <Building2 className="h-4 w-4" />
            Elan yerləşdir
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-3">
      {error ? (
        <p className="rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">{error}</p>
      ) : null}
      {listings.map((listing) => (
        <div
          key={listing.id}
          className="flex flex-col gap-4 rounded-2xl bg-surface p-3.5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70 sm:flex-row"
        >
          {listing.cover_image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={listing.cover_image}
              alt={listing.title}
              className="h-36 w-full shrink-0 rounded-xl object-cover sm:w-44"
            />
          ) : (
            <div className="flex h-36 w-full shrink-0 items-center justify-center rounded-xl bg-foreground/[0.04] text-foreground/30 sm:w-44">
              <Building2 className="h-8 w-8" />
            </div>
          )}

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={STATUS_BADGE[listing.status] ?? "neutral"}>
                {STATUS_LABELS[listing.status] ?? listing.status}
              </Badge>
              {listing.is_promoted ? (
                <Badge variant="gold">
                  <Star className="h-3 w-3" /> Tanıdılıb
                </Badge>
              ) : null}
            </div>
            <Link
              href={`/property/${listing.id}`}
              className="mt-1.5 line-clamp-1 font-semibold text-foreground transition-colors hover:text-brand"
            >
              {listing.title}
            </Link>
            <p className="mt-0.5 text-sm font-medium tabular-nums text-brand">
              {formatPrice(listing.price, listing.currency as "AZN" | "USD" | "EUR")}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {[listing.location_city, listing.location_district]
                .filter(Boolean)
                .join(", ")}{" "}
              · {listing.published_at ? formatDate(listing.published_at) : "Yayımlanmayıb"}
            </p>
            <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <Eye className="h-3.5 w-3.5" /> {listing.views}
              </span>
            </div>
          </div>

          <div className="flex shrink-0 flex-row gap-2 sm:flex-col sm:justify-center">
            <Link
              href={`/property/${listing.id}/edit`}
              className="rounded-xl bg-foreground/[0.05] px-3.5 py-2 text-[13px] font-medium text-foreground/80 transition-colors hover:bg-foreground/[0.09]"
            >
              Redaktə
            </Link>
            <button
              onClick={() => toggleStatus(listing)}
              disabled={busyId === listing.id}
              className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-foreground/[0.05] px-3.5 py-2 text-[13px] font-medium text-foreground/80 transition-colors hover:bg-foreground/[0.09] disabled:opacity-50"
            >
              {listing.status === "active" ? (
                <>
                  <PauseCircle className="h-4 w-4" /> Dayandır
                </>
              ) : (
                <>
                  <PlayCircle className="h-4 w-4" /> Aktiv et
                </>
              )}
            </button>
            <button
              onClick={() => remove(listing.id)}
              disabled={busyId === listing.id}
              aria-label="Elanı sil"
              className="inline-flex items-center justify-center rounded-xl bg-red-500/10 px-3.5 py-2 text-[13px] font-medium text-red-600 transition-colors hover:bg-red-500/15 disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
