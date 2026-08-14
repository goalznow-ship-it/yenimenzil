"use client";

import * as React from "react";
import Link from "next/link";
import { Skeleton, Badge, EmptyState } from "@yenimenzil/ui";
import {
  Building2,
  Eye,
  Trash2,
  PauseCircle,
  PlayCircle,
  Star,
  Copy,
  RefreshCw
} from "lucide-react";
import { dashboardApi, type MyPropertySummary, type PromotionCatalogItem } from "@/services/dashboard-api";
import { formatPrice, formatDate } from "@/lib/format";

const STATUS_BADGE: Record<string, React.ComponentProps<typeof Badge>["variant"]> = {
  active: "green",
  inactive: "neutral",
  pending: "amber",
  rejected: "red",
  archived: "neutral",
  draft: "neutral",
  expired: "neutral",
  sold: "neutral",
  rented: "neutral"
};

const STATUS_LABELS: Record<string, string> = {
  active: "Aktiv",
  inactive: "Deaktiv",
  pending: "Gözləmədə",
  rejected: "Rədd edilib",
  archived: "Arxivləşib",
  draft: "Qaralama",
  expired: "Vaxtı bitib",
  sold: "Satılıb",
  rented: "Kirayə verilib"
};

export function MyListingsTab() {
  const [listings, setListings] = React.useState<MyPropertySummary[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);
  const [busyId, setBusyId] = React.useState<string | null>(null);
  const [promoFor, setPromoFor] = React.useState<string | null>(null);
  const [catalog, setCatalog] = React.useState<PromotionCatalogItem[]>([]);

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
    dashboardApi
      .promotionCatalog()
      .then(setCatalog)
      .catch(() => undefined);
  }, [load]);

  const promote = async (listing: MyPropertySummary, tier: string) => {
    setBusyId(listing.id);
    setPromoFor(null);
    setError(null);
    setInfo(null);
    try {
      const result = await dashboardApi.purchasePromotion(listing.id, tier);
      setInfo(
        result.promotion_status === "active"
          ? `Elan tanıdılıb: ${result.promotion_status}`
          : result.detail
      );
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setBusyId(null);
    }
  };

  const toggleStatus = async (listing: MyPropertySummary) => {
    if (!listings) return;
    setBusyId(listing.id);
    setError(null);
    try {
      const updated =
        listing.status === "active"
          ? await dashboardApi.deactivateProperty(listing.id)
          : await dashboardApi.reactivateProperty(listing.id);
      setListings(
        listings.map((l) => (l.id === listing.id ? { ...l, status: updated.status } : l))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setBusyId(null);
    }
  };

  const renew = async (listing: MyPropertySummary) => {
    if (!listings) return;
    setBusyId(listing.id);
    setError(null);
    try {
      const updated = await dashboardApi.renewProperty(listing.id);
      setListings(
        listings.map((l) => (l.id === listing.id ? { ...l, status: updated.status } : l))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setBusyId(null);
    }
  };

  const duplicate = async (listing: MyPropertySummary) => {
    if (!listings) return;
    setBusyId(listing.id);
    setError(null);
    try {
      await dashboardApi.duplicateProperty(listing.id);
      load();
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
      {info ? (
        <p className="rounded-xl bg-emerald-500/10 px-3.5 py-2.5 text-[13px] text-emerald-700">
          {info}
        </p>
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
            {listing.status === "active" || listing.status === "archived" ? (
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
            ) : null}
            {listing.status === "expired" || listing.status === "rejected" ? (
              <button
                onClick={() => renew(listing)}
                disabled={busyId === listing.id}
                className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-foreground/[0.05] px-3.5 py-2 text-[13px] font-medium text-foreground/80 transition-colors hover:bg-foreground/[0.09] disabled:opacity-50"
              >
                <RefreshCw className="h-4 w-4" /> Yenilə
              </button>
            ) : null}
            {listing.status === "active" ? (
              <div className="relative">
                <button
                  onClick={() => setPromoFor(promoFor === listing.id ? null : listing.id)}
                  disabled={busyId === listing.id}
                  className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-foreground/[0.05] px-3.5 py-2 text-[13px] font-medium text-foreground/80 transition-colors hover:bg-foreground/[0.09] disabled:opacity-50"
                >
                  <Star className="h-4 w-4" /> Tanıt
                </button>
                {promoFor === listing.id ? (
                  <div className="absolute right-0 top-full z-10 mt-1.5 w-52 rounded-xl border border-border/70 bg-surface p-2 shadow-lg">
                    {catalog.map((item) => (
                      <button
                        key={item.tier}
                        onClick={() => promote(listing, item.tier)}
                        disabled={busyId === listing.id}
                        className="flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-[13px] font-medium transition-colors hover:bg-foreground/[0.05] disabled:opacity-50"
                      >
                        <span>{item.label}</span>
                        <span className="text-muted-foreground">
                          {formatPrice(item.price)}
                        </span>
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
            <button
              onClick={() => duplicate(listing)}
              disabled={busyId === listing.id}
              className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-foreground/[0.05] px-3.5 py-2 text-[13px] font-medium text-foreground/80 transition-colors hover:bg-foreground/[0.09] disabled:opacity-50"
            >
              <Copy className="h-4 w-4" /> Kopyala
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
