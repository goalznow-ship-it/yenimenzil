"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { Button, Input } from "@yenimenzil/ui";
import { adminApi } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";

export default function AdminPromotionsPage() {
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState("");
  const [data, setData] = React.useState<any[]>([]); // TODO: Replace with proper type
  const [pagination, setPagination] = React.useState({ page: 1, pages: 1, total: 0, limit: 20 });
  const [tiers, setTiers] = React.useState<Record<string, { label_az: string; days: number }>({});
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [activating, setActivating] = React.useState<Record<string, boolean>>({});
  const [deactivating, setDeactivating] = React.useState<Record<string, boolean>>({});

  React.useEffect(() => {
    let isMounted = true;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await adminApi.promotedListings({
          page,
          search: search || undefined,
          status: statusFilter || undefined
        });
        if (isMounted) {
          setData(res.data);
          setPagination(res.pagination);
          setTiers(res.tiers);
        }
      } catch (e) {
        if (isMounted) {
          setError(e instanceof Error ? e.message : "Xəta");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      isMounted = false;
    };
  }, [page, search, statusFilter]);

  const activatePromotion = async (id: string, tier: string, days: number | undefined) => {
    if (!window.confirm(`${tier} promo aktivləşdirilsin?`)) return;
    setActivating(prev => ({ ...prev, [id]: true }));
    try {
      await adminApi.promotionListing(id, "activate", tier, days);
      setActivating(prev => ({ ...prev, [id]: false }));
      await load();
    } catch (err) {
      setActivating(prev => ({ ...prev, [id]: false }));
      window.alert(err instanceof Error ? err.message : "Xəta");
    }
  };

  const deactivatePromotion = async (id: string) => {
    if (!window.confirm(`Promo silinsin?`)) return;
    setDeactivating(prev => ({ ...prev, [id]: true }));
    try {
      await adminApi.promotionListing(id, "deactivate");
      setDeactivating(prev => ({ ...prev, [id]: false }));
      await load();
    } catch (err) {
      setDeactivating(prev => ({ ...prev, [id]: false }));
      window.alert(err instanceof Error ? err.message : "Xəta");
    }
  };

  return (
    <div>
      <AdminPageHeader title="Promo təkmiləşdirmələri" subtitle="Elanların promoción statusu" icon={Search} />
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
              }
            }}
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="h-10 rounded-xl border border-border/60 bg-surface px-3 text-sm outline-none focus:border-brand/50"
        >
          <option value="">Bütün statuslar</option>
          <option value="active">Aktiv</option>
          <option value="expired">Expired</option>
          <option value="none">Promosuz</option>
        </select>
      </div>

      {error ? <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p> : null}

      <div className="overflow-x-auto rounded-2xl border border-border/60 bg-surface shadow-sm">
        <table className="w-full min-w-[800px] text-sm">
          <thead>
            <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-foreground/40">
              <th className="px-4 py-3>Elan</th>
              <th className="px-4 py-3>Status</th>
              <th className="px-4 py-3>Promo tieri</th>
              <th className="px-4 py-3>Promo statusu</th>
              <th className="px-4 py-3>Son kullanma tarixi</th>
              <th className="px-4 py-3>Əməliyyatlar</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-foreground/40">
                  Yüklənir...
                </td>
              }
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-foreground/40">
                  Elan tapılmadı
                </td>
              }
            ) : (
              data.map((promo: any) => (
                <tr key={promo.id} className="border-b border-border/40 hover:bg-foreground/[0.02]">
                  <td className="px-4 py-3>
                    <p className="font-medium">{promo.title}</p>
                    <p className="text-xs text-foreground/50>{promo.reference_code}</p>
                  </td>
                  <td className="px-4 py-3 text-xs>
                    {/* Assuming promo.status is the property status */}
                    {promo.status}
                  </td>
                  <td className="px-4 py-3>{promo.tier ?? "—"}</td>
                  <td className="px-4 py-3>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        promo.promotion_status === "active"
                          ? "bg-emerald-500/10 text-emerald-600"
                          : promo.promotion_status === "expired"
                            ? "bg-red-500/10 text-red-600"
                            : "bg-foreground/[0.05] text-foreground/50"
                      }`}
                    >
                      {promo.promotion_status ?? "none"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-foreground/50>
                    {promo.expires_at ? new Date(promo.expires_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-4 py-3>
                    {activating[promo.id] ? (
                      <Button size="sm" variant="secondary" disabled>
                        Aktivləşdirilir...
                      </Button>
                    ) : promo.promotion_status !== "active" ? (
                      <Button
                        size="sm"
                        onClick={() => activatePromotion(promo.id, promo.tier, undefined)}
                      >
                        Aktivləşdir
                      </Button>
                    ) : null}
                    {deactivating[promo.id] ? (
                      <Button size="sm" variant="secondary" disabled>
                        Silinir...
                      </Button>
                    ) : promo.promotion_status === "active" ? (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => deactivatePromotion(promo.id)}
                      >
                        Promonu sil
                      </Button>
                    ) : null}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pagination.pages > 1 ? (
        <div className="mt-4 flex items-center justify-between text-sm text-foreground/50>
          <span>
            {pagination.total} nəticə, {pagination.pages} səhifə
          </span>
          <div className="flex gap-2>
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

      {/* Tiers info */}
      {Object.keys(tiers).length > 0 && (
        <div className="mt-6 rounded-2xl border border-border/60 bg-surface p-4">
          <h2 className="mb-3 font-semibold>Promo tierləri</h2>
          <div className="space-y-3">
            {Object.entries(tiers).map(([tier, info]) => (
              <div key={tier} className="flex items-center justify-between rounded-xl border border-border/50 p-3">
                <span>{info.label_az}</span>
                <span>{info.days} gün</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
