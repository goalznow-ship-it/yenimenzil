"use client";

import * as React from "react";
import {
  Building,
  ClipboardCheck,
  ClipboardList,
  Clock,
  Flag,
  Home,
  Users
} from "lucide-react";
import { adminApi, type AdminStats } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";

function StatCard({
  label,
  value,
  icon: Icon,
  tone = "default"
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  tone?: "default" | "warn" | "danger" | "good";
}) {
  const tones = {
    default: "bg-foreground/[0.04] text-foreground/70",
    warn: "bg-amber-500/10 text-amber-600",
    danger: "bg-red-500/10 text-red-600",
    good: "bg-emerald-500/10 text-emerald-600"
  };
  return (
    <div className="rounded-2xl border border-border/60 bg-surface p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm text-foreground/50">{label}</p>
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${tones[tone]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
    </div>
  );
}

export default function AdminDashboardPage() {
  const [stats, setStats] = React.useState<AdminStats | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    adminApi
      .stats()
      .then(setStats)
      .catch((err) => setError(err instanceof Error ? err.message : "Xəta"));
  }, []);

  return (
    <div>
      <AdminPageHeader
        title="Ümumi baxış"
        subtitle="Marketplace vəziyyəti"
        icon={ClipboardCheck}
      />
      {error ? (
        <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p>
      ) : !stats ? (
        <div className="h-40 animate-pulse rounded-2xl bg-foreground/[0.04]" />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatCard label="Cəmi istifadəçilər" value={stats.total_users} icon={Users} />
            <StatCard label="Aktiv istifadəçilər" value={stats.active_users} icon={Users} tone="good" />
            <StatCard label="Cəmi elanlar" value={stats.total_listings} icon={ClipboardList} />
            <StatCard label="Aktiv elanlar" value={stats.active_listings} icon={Home} tone="good" />
            <StatCard label="Baxışda olan" value={stats.pending_review} icon={Clock} tone="warn" />
            <StatCard label="Rədd edilən" value={stats.rejected_listings} icon={ClipboardList} tone="danger" />
            <StatCard label="Satılan" value={stats.sold} icon={Building} />
            <StatCard label="Şikayətlər" value={stats.reports_open} icon={Flag} tone="warn" />
          </div>
        </div>
      )}
    </div>
  );
}