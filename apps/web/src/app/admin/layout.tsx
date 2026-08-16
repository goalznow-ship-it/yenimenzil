"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  Building2,
  ClipboardList,
  Flag,
  FolderCog,
  History,
  LayoutDashboard,
  LogOut,
  MapPin,
  Megaphone,
  TrendingUp,
  UserCheck,
  UsersRound,
  Wallet
} from "lucide-react";
import { cn } from "@yenimenzil/ui";
import { RequireAuth } from "@/components/auth/auth-provider";
import { isStaff, useAuth } from "@/store/auth";

const NAV = [
  { href: "/admin/dashboard", label: "Ümumi baxış", icon: LayoutDashboard },
  { href: "/admin/listings", label: "Elanlar", icon: ClipboardList },
  { href: "/admin/reports", label: "Şikayətlər", icon: Flag },
  { href: "/admin/users", label: "İstifadəçilər", icon: UsersRound },
  { href: "/admin/agencies", label: "Agentliklər", icon: Building2 },
  { href: "/admin/agents", label: "Agentlər", icon: UserCheck },
  { href: "/admin/promotions", label: "Promosiyalar", icon: Megaphone },
  { href: "/admin/payments", label: "Ödənişlər", icon: Wallet },
  { href: "/admin/analytics", label: "Analitika", icon: BarChart3 },
  { href: "/admin/features", label: "Kataloq", icon: FolderCog },
  { href: "/admin/locations", label: "Lokasiyalar", icon: MapPin },
  { href: "/admin/audit", label: "Audit jurnalı", icon: History }
];

export default function AdminLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);

  React.useEffect(() => {
    if (user && !isStaff(user.role)) {
      router.replace("/");
    }
  }, [user, router]);

  const handleLogout = async () => {
    await logout();
    router.replace("/");
  };

  return (
    <RequireAuth>
      <div className="mx-auto flex w-full max-w-7xl flex-1 gap-8 px-4 py-8 md:px-6">
        <aside className="hidden w-56 shrink-0 md:block">
          <div className="sticky top-24 space-y-1">
            <p className="px-3 pb-2 text-xs font-semibold uppercase tracking-wider text-foreground/40">
              Admin panel
            </p>
            {NAV.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-medium text-foreground/60 transition-colors hover:bg-foreground/[0.04] hover:text-foreground",
                    active && "bg-brand-soft text-brand"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
            <button
              type="button"
              onClick={handleLogout}
              className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-medium text-foreground/50 transition-colors hover:bg-foreground/[0.04] hover:text-foreground"
            >
              <LogOut className="h-4 w-4" />
              Çıxış
            </button>
          </div>
        </aside>

        {/* Mobile nav */}
        <div className="fixed bottom-16 left-0 right-0 z-30 border-t border-border/60 bg-surface/95 backdrop-blur md:hidden">
          <div className="flex justify-around overflow-x-auto py-1.5">
            {NAV.slice(0, 6).map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex flex-col items-center gap-0.5 px-2.5 py-1 text-[10px] font-medium text-foreground/50",
                    active && "text-brand"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label.split(" ")[0]}
                </Link>
              );
            })}
          </div>
        </div>

        <main className="min-w-0 flex-1 pb-10">{children}</main>
      </div>
    </RequireAuth>
  );
}

export function AdminPageHeader({
  title,
  subtitle,
  icon: Icon = TrendingUp
}: {
  title: string;
  subtitle?: string;
  icon?: React.ElementType;
}) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-brand">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
          {subtitle ? (
            <p className="text-sm text-foreground/50">{subtitle}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}