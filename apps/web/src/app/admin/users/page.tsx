"use client";

import * as React from "react";
import { Search, UserRound } from "lucide-react";
import { Button, Input } from "@yenimenzil/ui";
import { adminApi, type AdminUser } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";
import { useAuth } from "@/store/auth";

const ROLE_OPTIONS = [
  "user",
  "owner",
  "agent",
  "agency_admin",
  "moderator",
  "admin",
  "super_admin"
];

export default function AdminUsersPage() {
  const me = useAuth((s) => s.user);
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [role, setRole] = React.useState("");
  const [data, setData] = React.useState<AdminUser[]>([]);
  const [pagination, setPagination] = React.useState({ page: 1, pages: 1, total: 0, limit: 20 });
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const res = await adminApi.users({
        page,
        search: search || undefined,
        role: role || undefined
      });
      setData(res.data);
      setPagination(res.pagination);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xəta");
    } finally {
      setLoading(false);
    }
  }, [page, search, role]);

   React.useEffect(() => {
     // eslint-disable-next-line react-hooks/set-state-in-effect
     load();
     // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [page, role]);

  const toggleActive = async (u: AdminUser) => {
    if (!window.confirm(`${u.full_name} — istifadəçini ${u.is_active ? "deaktiv" : "aktiv"} et?`)) return;
    try {
      if (u.is_active) {
        await adminApi.userDeactivate(u.id);
      } else {
        await adminApi.userUpdate(u.id, { is_active: true });
      }
      await load();
    } catch (e) {
      window.alert(e instanceof Error ? e.message : "Xəta");
    }
  };

  const setUserRole = async (u: AdminUser, nextRole: string) => {
    try {
      await adminApi.userUpdate(u.id, { role: nextRole });
      await load();
    } catch (e) {
      window.alert(e instanceof Error ? e.message : "Xəta");
    }
  };

  return (
    <div>
      <AdminPageHeader title="İstifadəçilər" subtitle="Hesab idarəetməsi" icon={UserRound} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative min-w-52">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
          <Input
            className="pl-9"
            placeholder="Email və ya ad..."
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
        <select
          value={role}
          onChange={(e) => {
            setRole(e.target.value);
            setPage(1);
          }}
          className="h-10 rounded-xl border border-border/60 bg-surface px-3 text-sm outline-none focus:border-brand/50"
        >
          <option value="">Bütün rollar</option>
          {ROLE_OPTIONS.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      {err ? <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{err}</p> : null}

      <div className="overflow-x-auto rounded-2xl border border-border/60 bg-surface shadow-sm">
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-foreground/40">
              <th className="px-4 py-3">İstifadəçi</th>
              <th className="px-4 py-3">Rol</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Qeydiyyat</th>
              <th className="px-4 py-3">Əməliyyatlar</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-foreground/40">
                  Yüklənir...
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-foreground/40">
                  İstifadəçi tapılmadı
                </td>
              </tr>
            ) : (
              data.map((u) => (
                <tr key={u.id} className="border-b border-border/40 hover:bg-foreground/[0.02]">
                  <td className="px-4 py-3">
                    <p className="font-medium">{u.full_name}</p>
                    <p className="text-xs text-foreground/50">{u.email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={u.role}
                      disabled={me?.id === u.id}
                      onChange={(e) => setUserRole(u, e.target.value)}
                      className="rounded-lg border border-border/60 bg-surface px-2 py-1 text-xs outline-none focus:border-brand/50 disabled:opacity-50"
                    >
                      {ROLE_OPTIONS.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        u.is_active
                          ? "bg-emerald-500/10 text-emerald-600"
                          : "bg-red-500/10 text-red-600"
                      }`}
                    >
                      {u.is_active ? "Aktiv" : "Deaktiv"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-foreground/50">
                    {u.created_at ? u.created_at.slice(0, 10) : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={me?.id === u.id}
                      onClick={() => toggleActive(u)}
                    >
                      {u.is_active ? "Deaktiv et" : "Aktiv et"}
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