"use client";

import * as React from "react";
import Link from "next/link";
import { Check, Eye, Search, ShieldCheck, X } from "lucide-react";
import { Input, Button } from "@yenimenzil/ui";
import { adminApi, type AdminListing } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";

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

function formatPrice(price: number | null): string {
  return price != null ? `${Math.round(price).toLocaleString("az")} ₼` : "—";
}

export default function AdminListingsPage() {
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [status, setStatus] = React.useState("");
  const [data, setData] = React.useState<AdminListing[]>([]);
  const [pagination, setPagination] = React.useState({ page: 1, pages: 1, total: 0, limit: 20 });
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const [actingId, setActingId] = React.useState<string | null>(null);

  const load = React.useCallback(async (args: { page?: number; search?: string; status?: string } = {}) => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminApi.listings({
        page: args.page ?? page,
        search: args.search ?? (search || undefined),
        status: args.status ?? (status || undefined)
      });
      setData(res.data);
      setPagination(res.pagination);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta baş verdi");
    } finally {
      setLoading(false);
    }
  }, [page, search, status]);

   React.useEffect(() => {
     // eslint-disable-next-line react-hooks/set-state-in-effect
     load();
     // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [page, status]);

  const runAction = async (id: string, action: "approve" | "reject" | "suspend" | "archive") => {
    if (action === "approve" && !window.confirm("Elanı təsdiqləyin?")) return;
    if (action === "reject" && !window.confirm("Elanı rədd edin?")) return;
    setActingId(id);
    try {
      await adminApi.listingAction(id, action);
      await load();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Xəta");
    } finally {
      setActingId(null);
    }
  };

  const runBulk = async (action: "bulk-approve" | "bulk-suspend" | "bulk-archive") => {
    if (selected.size === 0) return;
    if (!window.confirm(`${selected.size} elan üzərində əməliyyat?`)) return;
    try {
      await adminApi.bulkListings(action, [...selected]);
      setSelected(new Set());
      await load();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Xəta");
    }
  };

  const toggle = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  return (
    <div>
      <AdminPageHeader title="Elanlar" subtitle="Moderasiya və idarəetmə" icon={ShieldCheck} />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative min-w-52">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
          <Input
            className="pl-9"
            placeholder="Elan axtar..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setPage(1);
                void load({ page: 1, search, status });
              }
            }}
          />
        </div>
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
          className="h-10 rounded-xl border border-border/60 bg-surface px-3 text-sm outline-none focus:border-brand/50"
        >
          <option value="">Bütün statuslar</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        {selected.size > 0 ? (
          <>
            <Button size="sm" onClick={() => runBulk("bulk-approve")}>
              <Check className="h-3.5 w-3.5" /> Təsdiqlə
            </Button>
            <Button size="sm" variant="secondary" onClick={() => runBulk("bulk-suspend")}>
              Dayandır
            </Button>
            <Button size="sm" variant="secondary" onClick={() => runBulk("bulk-archive")}>
              Arxivlə
            </Button>
            <span className="text-sm text-foreground/50">{selected.size} seçilib</span>
          </>
        ) : null}
      </div>

      {error ? (
        <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p>
      ) : null}

      <div className="overflow-x-auto rounded-2xl border border-border/60 bg-surface shadow-sm">
        <table className="w-full min-w-[760px] text-sm">
          <thead>
            <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-foreground/40">
              <th className="px-4 py-3" />
              <th className="px-4 py-3">Elan</th>
              <th className="px-4 py-3">Qiymət</th>
              <th className="px-4 py-3">Lokasiya</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Baxışlar</th>
              <th className="px-4 py-3">Əməliyyatlar</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-foreground/40">
                  Yüklənir...
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-foreground/40">
                  Elan tapılmadı
                </td>
              </tr>
            ) : (
              data.map((listing) => (
                <tr key={listing.id} className="border-b border-border/40 hover:bg-foreground/[0.02]">
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selected.has(listing.id)}
                      onChange={() => toggle(listing.id)}
                      className="accent-brand"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/admin/listings/${listing.id}`}
                      className="font-medium text-foreground hover:text-brand"
                    >
                      {listing.title}
                    </Link>
                    <p className="text-xs text-foreground/40">{listing.reference_code}</p>
                  </td>
                  <td className="px-4 py-3 font-medium">{formatPrice(listing.price)}</td>
                  <td className="px-4 py-3 text-foreground/60">
                    {listing.city}
                    {listing.district ? `, ${listing.district}` : ""}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        listing.status === "active"
                          ? "bg-emerald-500/10 text-emerald-600"
                          : listing.status === "pending_review"
                            ? "bg-amber-500/10 text-amber-600"
                            : listing.status === "rejected" || listing.status === "suspended"
                              ? "bg-red-500/10 text-red-600"
                              : "bg-foreground/[0.05] text-foreground/50"
                      }`}
                    >
                      {STATUS_LABELS[listing.status] ?? listing.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-foreground/50">
                    <span className="inline-flex items-center gap-1">
                      <Eye className="h-3.5 w-3.5" />
                      {listing.views}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <Link
                        href={`/admin/listings/${listing.id}`}
                        className="rounded-lg px-2 py-1 text-xs font-medium text-brand hover:bg-brand-soft"
                      >
                        Bax
                      </Link>
                      {listing.status === "pending_review" ? (
                        <>
                          <button
                            type="button"
                            disabled={actingId === listing.id}
                            onClick={() => runAction(listing.id, "approve")}
                            className="rounded-lg bg-emerald-500/10 px-2 py-1 text-xs font-medium text-emerald-600 hover:bg-emerald-500/20"
                          >
                            Təsdiqlə
                          </button>
                          <button
                            type="button"
                            disabled={actingId === listing.id}
                            onClick={() => runAction(listing.id, "reject")}
                            className="rounded-lg bg-red-500/10 px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-500/20"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </>
                      ) : null}
                      {listing.status === "active" ? (
                        <button
                          type="button"
                          disabled={actingId === listing.id}
                          onClick={() => runAction(listing.id, "suspend")}
                          className="rounded-lg bg-amber-500/10 px-2 py-1 text-xs font-medium text-amber-600 hover:bg-amber-500/20"
                        >
                          Dayandır
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pagination.pages > 1 ? (
        <div className="mt-4 flex items-center justify-between text-sm text-foreground/50">
          <span>
            {pagination.total} nəticə, {pagination.pages} səhifə
          </span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Əvvəlki
            </Button>
            <Button
              size="sm"
              variant="secondary"
              disabled={page >= pagination.pages}
              onClick={() => setPage((p) => p + 1)}
            >
              Növbəti
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}