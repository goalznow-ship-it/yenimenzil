"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { Button, Input } from "@yenimenzil/ui";
import { adminApi, type AgentReputation } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";

export default function AdminAgentsPage() {
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [data, setData] = React.useState<AgentReputation[]>([]);
  const [pagination, setPagination] = React.useState({ page: 1, pages: 1, total: 0, limit: 20 });
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
       const res = await adminApi.agentReputation({ page, search: search || undefined });
      setData(res.data);
      setPagination(res.pagination);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xəta");
    } finally {
      setLoading(false);
    }
  }, [page, search]);

   React.useEffect(() => {
     // eslint-disable-next-line react-hooks/set-state-in-effect
     load();
     // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [page, search]);

  return (
    <div>
      <AdminPageHeader title="Agentların reputationu" subtitle="AgentlərinQiymətləndirilməsi" icon={Search} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative min-w-52">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
          <Input
            className="pl-9"
            placeholder="Agent adı..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setPage(1);
                load();
              }
            }}
          />
        </div>
      </div>

      {error ? <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p> : null}

      <div className="overflow-x-auto rounded-2xl border border-border/60 bg-surface shadow-sm">
        <table className="w-full min-w-[800px] text-sm">
          <thead>
            <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-foreground/40">
              <th className="px-4 py-3">Agent</th>
              <th className="px-4 py-3">Agentlik</th>
              <th className="px-4 py-3">Təsdiqlənmə identitéti</th>
              <th className="px-4 py-3">Təsdiqlənmə telefunu</th>
              <th className="px-4 py-3">Elan sayı</th>
              <th className="px-4 py-3">Aktiv elanlar</th>
              <th className="px-4 py-3">Baxışlar</th>
              <th className="px-4 py-3">Reputation skoru</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-foreground/40">
                  Yüklənir...
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-foreground/40">
                  Agent tapılmadı
                </td>
              </tr>
            ) : (
              data.map((agent) => (
                <tr key={agent.id} className="border-b border-border/40 hover:bg-foreground/[0.02]">
                  <td className="px-4 py-3">
                    <p className="font-medium">{agent.name}</p>
                    <p className="text-xs text-foreground/50">{agent.email ?? "—"}</p>
                  </td>
                  <td className="px-4 py-3">{agent.agency_id ? "Var" : "Yox"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        agent.verified_identity
                          ? "bg-emerald-500/10 text-emerald-600"
                          : "bg-red-500/10 text-red-600"
                      }`}
                    >
                      {agent.verified_identity ? "Bəli" : "Xeyr"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        agent.verified_phone
                          ? "bg-emerald-500/10 text-emerald-600"
                          : "bg-red-500/10 text-red-600"
                      }`}
                    >
                      {agent.verified_phone ? "Bəli" : "Xeyr"}
                    </span>
                  </td>
                  <td className="px-4 py-3">{agent.listing_count}</td>
                  <td className="px-4 py-3">{agent.active_listings}</td>
                  <td className="px-4 py-3">{agent.total_views}</td>
                  <td className="px-4 py-3 font-medium">
                    {agent.reputation_score}
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