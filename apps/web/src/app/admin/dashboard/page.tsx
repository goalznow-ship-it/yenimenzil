"use client";

import * as React from "react";
import { LayoutDashboard, Users, ClipboardCheck, Home, Clock, Flag, Building } from "lucide-react";
import { adminApi, type AdminStats } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";

export default function AdminDashboardPage() {
  const [stats, setStats] = React.useState<AdminStats | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    adminApi.stats().then(setStats).catch((err) => setError(err instanceof Error ? err.message : "Xəta"));
  }, []);

  if (error) {
    return <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p>;
  }
  if (!stats) {
    return <div className="h-40 animate-pulse rounded-2xl bg-foreground/[0.04]" />;
  }

  return (
    <div>
      <AdminPageHeader title="Ümumi baxış" subtitle="Marketplace vəziyyatı" icon={LayoutDashboard} />
      {error ? (
        <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p>
      ) : !stats ? (
        <div className="h-40 animate-pulse rounded-2xl bg-foreground/[0.04]" />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-xl border p-4 bg-surface/50">
              <p className="text-sm text-foreground/60">Cəmi istifadəçilər</p>
              <p className="text-xl font-semibold">{stats.total_users}</p>
            </div>
            <div className="rounded-xl border p-4 bg-surface/50">
              <p className="text-sm text-foreground/60">Aktiv istifadəçilər</p>
              <p className="text-xl font-semibold" style={{ color: "rgba(16,185,129,0.80)" }}>{stats.active_users}</p>
            </div>
            <div className="rounded-xl border p-4 bg-surface/50">
              <p className="text-sm text-foreground/60">Cəmi elanlar</p>
              <p className="text-xl font-semibold">{stats.total_listings}</p>
            </div>
            <div className="rounded-xl border p-4 bg-surface/50">
              <p className="text-sm text-foreground/60">Aktiv elanlar</p>
              <p className="text-xl font-semibold">{stats.active_listings}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-xl border p-4 bg-surface/50">
              <p className="text-sm text-foreground/60">Baxışda olan</p>
              <p className="text-xl font-semibold">{stats.pending_review}</p>
            </div>
            <div className="rounded-xl border p-4 bg-surface/50">
              <p className="text-sm text-foreground/60">Rədd edilən</p>
              <p className="text-xl font-semibold" style={{ color: "rgba(239,68,68,0.80)" }}>{stats.rejected_listings}</p>
            </div>
            <div className="rounded-xl border p-4 bg-surface/50">
              <p className="text-sm text-foreground/60">Satılan</p>
              <p className="text-xl font-semibold">{stats.sold}</p>
            </div>
            <div className="rounded-xl border p-4 bg-surface/50">
              <p className="text-sm text-foreground/60">Şikayətlər</p>
              <p className="text-xl font-semibold">{stats.reports_open}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
