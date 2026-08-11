"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ChevronDown,
  LayoutDashboard,
  LogOut,
  Plus,
  Settings,
  ShieldCheck,
  UserRound
} from "lucide-react";
import { cn } from "@yenimenzil/ui";
import { isStaff, useAuth } from "@/store/auth";

function initialsOf(name: string): string {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function UserMenu() {
  const [open, setOpen] = React.useState(false);
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const router = useRouter();

  const handleLogout = async () => {
    setOpen(false);
    await logout();
    router.push("/");
    router.refresh();
  };

  if (!user) return null;

  const items = [
    { href: "/dashboard", label: "İdarə paneli", icon: LayoutDashboard },
    { href: "/profile", label: "Profil", icon: Settings },
    ...(isStaff(user.role)
      ? [{ href: "/admin/listings", label: "Moderasiya", icon: ShieldCheck }]
      : [])
  ];

  return (
    <div className="relative hidden md:block">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="flex h-10 items-center gap-1.5 rounded-xl px-2 text-foreground/70 transition-colors hover:bg-foreground/[0.05]"
      >
        {user.profile?.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={user.profile.avatar_url}
            alt={user.full_name}
            className="h-7 w-7 rounded-full object-cover"
          />
        ) : (
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-soft text-[11px] font-semibold text-brand">
            {initialsOf(user.full_name)}
          </span>
        )}
        <ChevronDown className="h-3.5 w-3.5" />
      </button>

      {open ? (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute right-0 top-full z-50 mt-1 w-56 rounded-xl border border-border bg-surface p-1.5 shadow-panel">
            <div className="border-b border-border/70 px-3 py-2.5">
              <p className="truncate text-sm font-semibold text-foreground">
                {user.full_name}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {user.email}
              </p>
            </div>
            <div className="pt-1.5">
              {items.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground/75 transition-colors hover:bg-brand-soft hover:text-brand"
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              ))}
              <Link
                href="/add-property"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground/75 transition-colors hover:bg-brand-soft hover:text-brand"
              >
                <Plus className="h-4 w-4" />
                Elan yerləşdir
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className={cn(
                  "flex w-full items-center gap-2.5 rounded-lg px-3 py-2",
                  "text-sm text-red-600 transition-colors hover:bg-red-500/10"
                )}
              >
                <LogOut className="h-4 w-4" />
                Çıxış
              </button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}

export function UserAvatarLink() {
  const status = useAuth((s) => s.status);
  const user = useAuth((s) => s.user);

  if (status === "authenticated" && user) {
    return (
      <Link
        href="/dashboard"
        aria-label="Profil"
        className="flex h-10 w-10 items-center justify-center rounded-xl text-foreground/60 transition-colors hover:bg-foreground/[0.05] hover:text-foreground"
      >
        {user.profile?.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={user.profile.avatar_url}
            alt={user.full_name}
            className="h-7 w-7 rounded-full object-cover"
          />
        ) : (
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-soft text-[11px] font-semibold text-brand">
            {initialsOf(user.full_name)}
          </span>
        )}
      </Link>
    );
  }
  return (
    <Link
      href="/login"
      aria-label="Profil"
      className="flex h-10 w-10 items-center justify-center rounded-xl text-foreground/60 transition-colors hover:bg-foreground/[0.05] hover:text-foreground"
    >
      <UserRound className="h-[19px] w-[19px]" />
    </Link>
  );
}
