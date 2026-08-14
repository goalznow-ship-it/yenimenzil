"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ChevronDown,
  Globe,
  Heart,
  Menu,
  MessageCircle,
  Plus,
  Scale,
  Search,
  X
} from "lucide-react";
import { Button, cn } from "@yenimenzil/ui";
import { Logo } from "./logo";
import { UserAvatarLink, UserMenu } from "./user-menu";
import { LANGUAGE_OPTIONS } from "@/lib/languages";
import { useComparisonStore } from "@/stores/comparison-store";
import { useI18n } from "@/components/i18n-provider";
import type { Locale, MessageKey } from "@/lib/i18n";

function CompareLink() {
  const count = useComparisonStore((s) => s.ids.length);
  const { t } = useI18n();
  return (
    <Link
      href="/compare"
      aria-label={t("nav.compare")}
      className="relative flex h-10 w-10 items-center justify-center rounded-xl text-foreground/60 transition-colors hover:bg-foreground/[0.05] hover:text-foreground"
    >
      <Scale className="h-[19px] w-[19px]" />
      {count > 0 ? (
        <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand px-1 text-[10px] font-bold text-white">
          {count}
        </span>
      ) : null}
    </Link>
  );
}

const NAV_LINKS: Array<{ label: MessageKey; href: string }> = [
  { label: "nav.sale", href: "/search?deal=sale" },
  { label: "nav.rent", href: "/search?deal=rent" },
  { label: "nav.daily", href: "/search?deal=daily" },
  { label: "nav.newBuildings", href: "/search?deal=sale&property_type=new_building" },
  { label: "nav.house", href: "/search?deal=sale&property_type=house" },
  { label: "nav.villa", href: "/search?deal=sale&property_type=villa" },
  { label: "nav.land", href: "/search?deal=sale&property_type=land" },
  { label: "nav.commercial", href: "/search?deal=sale&property_type=commercial" }
];

function NavLink({
  href,
  label,
  onNavigate
}: {
  href: string;
  label: string;
  onNavigate?: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onNavigate}
      className="relative rounded-lg px-2.5 py-1.5 text-[13.5px] font-medium text-foreground/65 transition-colors hover:bg-foreground/[0.05] hover:text-foreground"
    >
      {label}
    </Link>
  );
}

export function Header() {
  const [scrolled, setScrolled] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [langOpen, setLangOpen] = React.useState(false);
  const { locale, setLocale, t } = useI18n();
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", onScroll, { passive: true });
    const initial = window.requestAnimationFrame(onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.cancelAnimationFrame(initial);
    };
  }, []);

  const [lastPathname, setLastPathname] = React.useState(pathname);
  if (lastPathname !== pathname) {
    setLastPathname(pathname);
    setMobileOpen(false);
    setLangOpen(false);
  }

  return (
    <header
      className={cn(
        "sticky top-0 z-40 border-b transition-all duration-200",
        scrolled || mobileOpen
          ? "border-border bg-background/90 shadow-[0_1px_0_rgba(20,23,22,0.02)] backdrop-blur-md"
          : "border-transparent bg-background"
      )}
    >
      <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between gap-4 px-4 lg:px-6">
        <div className="flex items-center gap-2">
          <button
            type="button"
            aria-label={t("nav.menu")}
            className="rounded-lg p-2 text-foreground/70 hover:bg-foreground/[0.05] lg:hidden"
            onClick={() => setMobileOpen((v) => !v)}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <Logo />
        </div>

        <nav
          aria-label={t("nav.main")}
          className="hidden items-center gap-0.5 xl:flex"
        >
          {NAV_LINKS.map((link) => (
            <NavLink key={link.href} href={link.href} label={t(link.label)} />
          ))}
        </nav>

        <div className="flex items-center gap-1.5">
          <Link
            href="/search"
            aria-label={t("nav.search")}
            className="hidden h-10 w-10 items-center justify-center rounded-xl text-foreground/60 transition-colors hover:bg-foreground/[0.05] hover:text-foreground md:flex"
          >
            <Search className="h-[19px] w-[19px]" />
          </Link>
          <Link
            href="/favorites"
            aria-label={t("nav.favorites")}
            className="flex h-10 w-10 items-center justify-center rounded-xl text-foreground/60 transition-colors hover:bg-foreground/[0.05] hover:text-foreground"
          >
            <Heart className="h-[19px] w-[19px]" />
          </Link>
          <CompareLink />
          <Link
            href="/messages"
            aria-label={t("nav.messages")}
            className="hidden h-10 w-10 items-center justify-center rounded-xl text-foreground/60 transition-colors hover:bg-foreground/[0.05] hover:text-foreground md:flex"
          >
            <MessageCircle className="h-[19px] w-[19px]" />
          </Link>

          <div className="relative hidden md:block">
            <button
              type="button"
              aria-haspopup="menu"
              aria-expanded={langOpen}
              className="flex h-10 items-center gap-1 rounded-xl px-2.5 text-[13px] font-medium text-foreground/60 transition-colors hover:bg-foreground/[0.05] hover:text-foreground"
              onClick={() => setLangOpen((v) => !v)}
            >
              <Globe className="h-4 w-4" />
              {locale.toUpperCase()}
              <ChevronDown className="h-3.5 w-3.5" />
            </button>
            {langOpen ? (
              <div className="absolute right-0 top-full z-50 mt-1 w-32 rounded-xl border border-border bg-surface p-1 shadow-panel">
                {LANGUAGE_OPTIONS.map((lang) => (
                  <button
                    key={lang.code}
                    type="button"
                    className={cn(
                      "flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors hover:bg-brand-soft",
                      locale.toUpperCase() === lang.code && "text-brand"
                    )}
                    onClick={() => {
                      setLocale(lang.code.toLowerCase() as Locale);
                      setLangOpen(false);
                      router.refresh();
                    }}
                  >
                    {lang.label}
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          <Link
            href="/add-property"
            aria-label={t("action.addListing")}
            className="hidden sm:block"
          >
            <Button size="sm" className="gap-1.5">
              <Plus className="h-4 w-4" />
              {t("action.addListing")}
            </Button>
          </Link>

          <UserAvatarLink />
          <UserMenu />
        </div>
      </div>

      {mobileOpen ? (
        <div className="border-t border-border bg-background px-4 py-3 lg:hidden">
          <nav
            aria-label={t("nav.main")}
            className="grid grid-cols-2 gap-1"
          >
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="rounded-xl px-3 py-2.5 text-sm font-medium text-foreground/70 transition-colors hover:bg-brand-soft hover:text-brand"
              >
                {t(link.label)}
              </Link>
            ))}
          </nav>
          <div className="mt-3 flex items-center gap-2 border-t border-border pt-3">
            {LANGUAGE_OPTIONS.map((lang) => (
              <button
                key={lang.code}
                type="button"
                onClick={() => {
                  setLocale(lang.code.toLowerCase() as Locale);
                  setMobileOpen(false);
                  router.refresh();
                }}
                className={cn(
                  "rounded-lg border px-3 py-1.5 text-[13px] font-medium transition-colors",
                  locale.toUpperCase() === lang.code
                    ? "border-brand/30 bg-brand-soft text-brand"
                    : "border-border text-foreground/70"
                )}
              >
                {lang.label}
              </button>
            ))}
            <Link
              href="/login"
              className="ml-auto rounded-lg border border-border px-3 py-1.5 text-[13px] font-medium text-foreground/70 transition-colors hover:border-foreground/25"
            >
              {t("nav.profile")}
            </Link>
          </div>
        </div>
      ) : null}
    </header>
  );
}
