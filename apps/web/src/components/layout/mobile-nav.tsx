"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Heart, Home, Plus, Search, UserRound } from "lucide-react";
import { cn } from "@yenimenzil/ui";
import { useI18n } from "@/components/i18n-provider";
import type { MessageKey } from "@/lib/i18n";

const ITEMS: Array<{ label: MessageKey; href: string; icon: typeof Home; emphasized?: boolean }> = [
  { label: "nav.home", href: "/", icon: Home },
  { label: "nav.search", href: "/search", icon: Search },
  { label: "nav.add", href: "/login", icon: Plus, emphasized: true },
  { label: "nav.favorites", href: "/favorites", icon: Heart },
  { label: "nav.profile", href: "/login", icon: UserRound }
];

export function MobileNav() {
  const pathname = usePathname();
  const { t } = useI18n();

  return (
    <nav
      aria-label={t("nav.main")}
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-surface/95 pb-[env(safe-area-inset-bottom)] shadow-[0_-4px_20px_rgba(20,23,22,0.06)] backdrop-blur-md md:hidden"
    >
      <div className="mx-auto flex max-w-md items-stretch justify-between px-2 py-1.5">
        {ITEMS.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              href={item.href}
              aria-label={t(item.label)}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex min-w-[56px] flex-col items-center gap-0.5 rounded-xl px-2 py-1.5 text-[10.5px] font-medium transition-colors",
                active
                  ? "text-brand"
                  : "text-foreground/55 hover:text-foreground"
              )}
            >
              {item.emphasized ? (
                <span className="-mt-4 flex h-11 w-11 items-center justify-center rounded-full bg-brand text-white shadow-lg shadow-brand/25">
                  <Icon className="h-5 w-5" strokeWidth={2.2} />
                </span>
              ) : (
                <Icon className="h-[22px] w-[22px]" strokeWidth={active ? 2.2 : 1.8} />
              )}
              <span className={item.emphasized ? "mt-0.5 font-semibold" : ""}>
                {t(item.label)}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
