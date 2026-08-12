"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { Button, Input } from "@yenimenzil/ui";
import { adminApi, type AgencyRow } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";

export default function AdminAgenciesPage() {
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [data, setData] = React.useState<AgencyRow[]>([]);
  const [pagination, setPagination] = React.useState({ page: 1, pages: 1, total: 0, limit: 20 });
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async (args: { page?: number; search?: string } = {}) => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminApi.agencies({
        page: args.page ?? page,
        search: args.search ?? (search || undefined)
      });
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

  const toggleVerification = async (agency: AgencyRow) => {
    if (!window.confirm(`${agency.name} — təsdiqləmə statusunu ${agency.is_verified ? "geri alır" : "verir"}?`)) return;
    try {
      await adminApi.agencyUpdate(agency.id, { is_verified: !agency.is_verified });
      await load();
    } catch (e) {
      window.alert(e instanceof Error ? e.message : "Xəta");
    }
  };

  return (
    <div>
      <AdminPageHeader title="Agentliklər" subtitle="Agentlik idarəetməsi" icon={Search} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative min-w-52">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
          <Input
            className="pl-9"
            placeholder="Agentlik adı..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setPage(1);
                void load({ page: 1, search });
              }
            }}
          />
        </div>
      </div>

      {error ? <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p> : null}

      <div className="overflow-x-auto rounded-2xl border border-border/60 bg-surface shadow-sm">
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-foreground/40">
              <th className="px-4 py-3">Agentlik</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Telefon</th>
              <th className="px-4 py-3">Vebsayt</th>
              <th className="px-4 py-3">Təsdiqləmə</th>
              <th className="px-4 py-3">Yaradılma tarixi</th>
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
                   Agentlik tapılmadı
                 </td>
               </tr>
             ) : (
              data.map((agency) => (
                <tr key={agency.id} className="border-b border-border/40 hover:bg-foreground/[0.02]">
                  <td className="px-4 py-3">
                    <p className="font-medium">{agency.name}</p>
                    <p className="text-xs text-foreground/50">{agency.slug}</p>
                  </td>
                  <td className="px-4 py-3">{agency.email ?? "—"}</td>
                  <td className="px-4 py-3">{agency.phone ?? "—"}</td>
                  <td className="px-4 py-3">{agency.website ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        agency.is_verified
                          ? "bg-emerald-500/10 text-emerald-600"
                          : "bg-red-500/10 text-red-600"
                      }`}
                    >
                      {agency.is_verified ? "Təsdiqlənib" : "Təsdiqlənməyib"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-foreground/50">
                    {agency.created_at ? agency.created_at.slice(0, 10) : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => toggleVerification(agency)}
                    >
                      {agency.is_verified ? "Təsdiqləməni geri al" : "Təsdiqlə"}
                    </Button>
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