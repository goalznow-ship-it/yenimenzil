"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { Button, Input } from "@yenimenzil/ui";
import { adminApi, type AuditEntry } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";

const ACTION_OPTIONS = [
  "user.update",
  "user.deactivate",
  "agency.update",
  "agency.deactivate",
  "feature.create",
  "feature.update",
  "feature.delete",
  "promotion.activate",
  "promotion.deactivate",
  "deleted",
  "moderation.approved",
  "moderation.rejected",
  "moderation.changes_requested",
  "moderation.suspended",
  "moderation.activated",
  "moderation.archived"
];

export default function AdminAuditPage() {
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [actionFilter, setActionFilter] = React.useState("");
  const [entityTypeFilter, setEntityTypeFilter] = React.useState("");
  const [data, setData] = React.useState<AuditEntry[]>([]);
  const [entityTypes, setEntityTypes] = React.useState<string[]>([]);
  const [pagination, setPagination] = React.useState({ page: 1, pages: 1, total: 0, limit: 50 });
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let isMounted = true;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await adminApi.auditLogs({
          page,
          action: actionFilter || undefined,
          entity_type: entityTypeFilter || undefined
        });
        if (isMounted) {
          setData(res.data);
          setPagination(res.pagination);
          setEntityTypes(res.filters.entity_types);
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
  }, [page, actionFilter, entityTypeFilter]);

  const filtered = search
    ? data.filter((entry) =>
        [entry.actor, entry.action, entry.entity_type, entry.entity_id]
          .filter(Boolean)
          .some((v) => v!.toLowerCase().includes(search.toLowerCase()))
      )
    : data;

  return (
    <div>
      <AdminPageHeader title="Audit logları" subtitle="Sistem əməliyyatların tarixçəsi" icon={Search} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative min-w-52">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
          <Input
            className="pl-9"
            placeholder="Axtar..."
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
          value={actionFilter}
          onChange={(e) => {
            setActionFilter(e.target.value);
            setPage(1);
          }}
          className="h-10 rounded-xl border border-border/60 bg-surface px-3 text-sm outline-none focus:border-brand/50"
        >
          <option value="">Bütün əməliyyatlar</option>
          {ACTION_OPTIONS.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
        <select
          value={entityTypeFilter}
          onChange={(e) => {
            setEntityTypeFilter(e.target.value);
            setPage(1);
          }}
          className="h-10 rounded-xl border border-border/60 bg-surface px-3 text-sm outline-none focus:border-brand/50"
        >
          <option value="">Bütün varliq tipleri</option>
          {entityTypes.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {error ? <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p> : null}

      <div className="overflow-x-auto rounded-2xl border border-border/60 bg-surface shadow-sm">
        <table className="w-full min-w-[900px] text-sm">
          <thead>
            <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-foreground/40">
              <th className="px-4 py-3">İtirən</th>
              <th className="px-4 py-3">Əməliyyat</th>
              <th className="px-4 py-3">Varlıq tipi</th>
              <th className="px-4 py-3">Varlıq ID</th>
              <th className="px-4 py-3">Ətraflı</th>
              <th className="px-4 py-3">Mənbə</th>
              <th className="px-4 py-3">Tarix</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-foreground/40">
                  Yüklənir...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-foreground/40">
                  Audit logu tapılmadı
                </td>
              </tr>
            ) : (
              filtered.map((entry) => (
                <tr key={entry.id} className="border-b border-border/40 hover:bg-foreground/[0.02]">
                  <td className="px-4 py-3">{entry.actor ?? "Sistem"}</td>
                  <td className="px-4 py-3">{entry.action}</td>
                  <td className="px-4 py-3">{entry.entity_type}</td>
                  <td className="px-4 py-3">{entry.entity_id ?? "—"}</td>
                  <td className="px-4 py-3">
                    {/* TODO: Format details */}
                    {JSON.stringify(entry.details)}
                  </td>
                  <td className="px-4 py-3">
                    {entry.source === "admin_actions" ? "Admin acciones" : "Moderasiyə"}
                  </td>
                  <td className="px-4 py-3 text-xs text-foreground/50">
                    {entry.created_at ? entry.created_at.slice(0, 16) : "—"}
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