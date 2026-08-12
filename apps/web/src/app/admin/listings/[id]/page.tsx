"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  Copy,
  Eye,
  Star,
  X
} from "lucide-react";
import { Button } from "@yenimenzil/ui";
import { adminApi, ComparableListing, PropertyDetail } from "@/services/admin-api";
import { AdminPageHeader } from "../../layout";

const STATUS_LABELS: Record<string, string> = {
  draft: "Qaralama",
  pending_review: "Baxışda",
  active: "Aktiv",
  rejected: "Rədd edilib",
  expired: "Vaxtı keçib",
  sold: "Satılıb",
  rented: "Kirayə verilib",
  archived: "Arxivdə",
  suspended: "Dayandırılıb"
};

const ACTION_LABELS: Record<string, string> = {
  approved: "Təsdiqləndi",
  rejected: "Rədd edildi",
  changes_requested: "Dəyişiklik tələb olundu",
  suspended: "Dayandırıldı",
  activated: "Aktivləşdirildi",
  archived: "Arxivləndi"
};

export default function AdminListingDetailPage() {
  const params = useParams<{ id: string }>();
  const [detail, setDetail] = React.useState<PropertyDetail | null>(null);
  const [comparables, setComparables] = React.useState<ComparableListing[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [acting, setActing] = React.useState<string | null>(null);
  const [promoMsg, setPromoMsg] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setError(null);
    try {
      const d = await adminApi.listingDetail(params.id);
      setDetail(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta baş verdi");
    }
  }, [params.id]);

  React.useEffect(() => {
    void load();
  }, [load]);

  const runAction = async (
    action: "approve" | "reject" | "suspend" | "archive" | "mark-sold"
  ) => {
    if (!window.confirm(`Əməliyyat: ${ACTION_LABELS[action] ?? action} — davam edilsin?`)) return;
    setActing(action);
    try {
      await adminApi.listingAction(params.id, action);
      setDetail(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setActing(null);
    }
  };

  const promote = async (tier: string) => {
    setActing("promote");
    setPromoMsg(null);
    try {
      await adminApi.promotionListing(params.id, "activate", tier);
      setPromoMsg(`Promo "${tier}" aktivləşdirildi`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setActing(null);
    }
  };

  const loadComparables = async () => {
    try {
      const res = await adminApi.comparables(params.id);
      setComparables(res.comparables);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    }
  };

  if (error) {
    return (
      <div>
        <AdminPageHeader title="Elan detalları" />
        <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!detail) {
    return (
      <div>
        <AdminPageHeader title="Elan detalları" />
        <div className="h-60 animate-pulse rounded-2xl bg-foreground/[0.04]" />
      </div>
    );
  }

  return (
    <div>
      <Link
        href="/admin/listings"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-foreground/50 hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> Elanlara qayıt
      </Link>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{detail.title}</h1>
          <p className="mt-0.5 text-sm text-foreground/50">
            {detail.reference_code} · {detail.currency}
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            void navigator.clipboard.writeText(detail.id);
          }}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border/60 px-2.5 py-1.5 text-xs text-foreground/50 hover:text-foreground"
        >
          <Copy className="h-3 w-3" /> ID
        </button>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <InfoCard detail={detail} />

          {detail.duplicate_signals?.length > 0 ? (
            <div className="rounded-2xl border border-amber-500/30 bg-amber-500/[0.04] p-4">
              <h2 className="mb-3 flex items-center gap-2 font-semibold">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Dublikat ehtimalları
              </h2>
              <div className="space-y-2">
                {detail.duplicate_signals.map((sig) => (
                  <div
                    key={sig.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border/50 bg-surface p-3"
                  >
                    <div>
                      <Link
                        href={`/admin/listings/${sig.id}`}
                        className="font-medium hover:text-brand"
                      >
                        {sig.title}
                      </Link>
                      <p className="text-xs text-foreground/50">
                        {sig.reference_code} · {sig.rooms} otaq · {sig.area_total} m²
                      </p>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      {sig.same_owner ? (
                        <span className="rounded-full bg-foreground/[0.05] px-2 py-0.5 text-xs">
                          Eyni sahib
                        </span>
                      ) : null}
                      <span
                        className={`font-semibold ${
                          sig.confidence >= 70 ? "text-red-600" : "text-amber-600"
                        }`}
                      >
                        {sig.confidence}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {comparables ? (
            <div className="rounded-2xl border border-border/60 bg-surface p-4 shadow-sm">
              <h2 className="mb-3 font-semibold">Oxşar elanlar ({comparables.length})</h2>
              {comparables.length === 0 ? (
                <p className="text-sm text-foreground/50">Oxşar elan tapılmadı</p>
              ) : (
                <div className="space-y-2">
                  {comparables.map((c) => (
                    <div
                      key={c.id}
                      className="flex items-center justify-between rounded-xl border border-border/50 p-3"
                    >
                      <div>
                        <Link
                          href={`/admin/listings/${c.id}`}
                          className="font-medium hover:text-brand"
                        >
                          {c.title}
                        </Link>
                        <p className="text-xs text-foreground/50">
                          {c.district ?? c.city} · {c.price_per_m2 != null ? `${c.price_per_m2} ₼/m²` : ""}
                        </p>
                      </div>
                      <p className="font-medium">{c.price != null ? `${c.price.toLocaleString("az")} ₼` : "—"}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </div>

        <div className="space-y-4">
          <div className="rounded-2xl border border-border/60 bg-surface p-4 shadow-sm">
            <h2 className="mb-3 font-semibold">Moderasiya</h2>
            <div className="flex flex-wrap gap-2">
              <StatusPill status={detail.status} />
              {detail.is_promoted || detail.is_premium ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-purple-500/10 px-2 py-0.5 text-xs font-medium text-purple-600">
                  <Star className="h-3 w-3" /> Promo
                </span>
              ) : null}
            </div>
            <div className="mt-4 space-y-2">
              {detail.analytics?.views != null ? (
                <p className="flex items-center gap-2 text-sm text-foreground/60">
                  <Eye className="h-4 w-4" /> {detail.analytics.views} baxış
                </p>
              ) : null}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {detail.status === "pending_review" ? (
                <Button size="sm" disabled={!!acting} onClick={() => runAction("approve")}>
                  <Check className="h-3.5 w-3.5" /> Təsdiqlə
                </Button>
              ) : null}
              {detail.status === "pending_review" || detail.status === "active" ? (
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={!!acting}
                  onClick={() => runAction("reject")}
                >
                  <X className="h-3.5 w-3.5" /> Rədd et
                </Button>
              ) : null}
              {detail.status === "active" ? (
                <Button size="sm" variant="secondary" disabled={!!acting} onClick={() => runAction("suspend")}>
                  Dayandır
                </Button>
              ) : null}
              {detail.status === "active" ? (
                <Button size="sm" variant="secondary" disabled={!!acting} onClick={() => runAction("mark-sold")}>
                  Satıldı
                </Button>
              ) : null}
              <Button
                size="sm"
                variant="secondary"
                disabled={!!acting}
                onClick={() => runAction("archive")}
              >
                Arxivlə
              </Button>
            </div>
          </div>

          <div className="rounded-2xl border border-border/60 bg-surface p-4 shadow-sm">
            <h2 className="mb-3 font-semibold">Promo</h2>
            <div className="grid grid-cols-2 gap-2">
              {["standard", "premium", "vip", "urgent"].map((tier) => (
                <Button
                  key={tier}
                  size="sm"
                  variant="secondary"
                  disabled={!!acting}
                  onClick={() => promote(tier)}
                >
                  {tier}
                </Button>
              ))}
            </div>
            {promoMsg ? <p className="mt-2 text-xs text-emerald-600">{promoMsg}</p> : null}
            <Button
              size="sm"
              variant="secondary"
              className="mt-2 w-full"
              disabled={!!acting}
              onClick={async () => {
                try {
                  await adminApi.promotionListing(params.id, "deactivate");
                  setPromoMsg("Promo silindi");
                  await load();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Xəta");
                }
              }}
            >
              Promonu sil
            </Button>
          </div>

          <div className="rounded-2xl border border-border/60 bg-surface p-4 shadow-sm">
            <h2 className="mb-3 font-semibold">Şikayətlər ({detail.reports.length})</h2>
            {detail.reports.length === 0 ? (
              <p className="text-sm text-foreground/50">Şikayət yoxdur</p>
            ) : (
              <div className="space-y-2">
                {detail.reports.slice(0, 5).map((report) => (
                  <div key={report.id} className="rounded-xl border border-border/50 p-3 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{report.reason}</span>
                      <span className="text-xs text-foreground/40">{report.status}</span>
                    </div>
                    {report.description ? (
                      <p className="mt-1 text-xs text-foreground/60">{report.description}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={loadComparables}
            className="w-full rounded-2xl border border-dashed border-border/80 p-3 text-sm text-foreground/60 hover:border-brand/50 hover:text-brand"
          >
            Oxşar elanları göstər
          </button>
        </div>
      </div>

      {detail.moderation_timeline?.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-border/60 bg-surface p-4 shadow-sm">
          <h2 className="mb-3 font-semibold">Moderasiya tarixçəsi</h2>
          <div className="space-y-2">
            {detail.moderation_timeline.map((entry) => (
              <div key={entry.id} className="flex items-start justify-between gap-3 text-sm">
                <div>
                  <span className="font-medium">{ACTION_LABELS[entry.what] ?? entry.what}</span>
                  {entry.reason ? (
                    <p className="text-xs text-foreground/50">{entry.reason}</p>
                  ) : null}
                </div>
                <div className="text-right">
                  <p className="text-xs text-foreground/50">{entry.who}</p>
                  <p className="text-xs text-foreground/40">{entry.timestamp}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const tones: Record<string, string> = {
    active: "bg-emerald-500/10 text-emerald-600",
    pending_review: "bg-amber-500/10 text-amber-600",
    rejected: "bg-red-500/10 text-red-600",
    suspended: "bg-red-500/10 text-red-600",
    sold: "bg-blue-500/10 text-blue-600"
  };
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
        tones[status] ?? "bg-foreground/[0.05] text-foreground/50"
      }`}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

function InfoCard({ detail }: { detail: PropertyDetail }) {
  const rows: [string, string][] = [
    ["Sahib", detail.seller?.full_name ?? "—"],
    ["Email", detail.seller?.email ?? "—"],
    ["Qiymət", `${detail.price.toLocaleString("az")} ${detail.currency}`],
    ["Otaqlar", String(detail.rooms)],
    ["Sahə", `${detail.area_total} m²`],
    ["Mərtəbə", detail.floor != null ? `${detail.floor}/${detail.total_floors ?? "?"}` : "—"],
    ["Ünvan", detail.location?.address_text ?? "—"],
    ["Rayon", [detail.location?.city, detail.location?.district].filter(Boolean).join(", ") || "—"],
    ["Metro", detail.location?.metro ?? "—"],
    ["Yaradılıb", detail.created_at ?? "—"]
  ];
  return (
    <div className="rounded-2xl border border-border/60 bg-surface p-4 shadow-sm">
      <h2 className="mb-3 font-semibold">Məlumat</h2>
      <dl className="grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 border-b border-border/40 pb-2">
            <dt className="text-foreground/50">{label}</dt>
            <dd className="truncate text-right font-medium">{value}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 line-clamp-3 text-sm text-foreground/60">{detail.description}</p>
    </div>
  );
}