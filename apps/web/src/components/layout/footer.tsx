"use client";

import Link from "next/link";
import { Logo } from "./logo";
import { useI18n } from "@/components/i18n-provider";
import type { MessageKey } from "@/lib/i18n";

const FOOTER_COLUMNS: Array<{ title: MessageKey; links: Array<{ label: MessageKey; href: string }> }> = [
  {
    title: "footer.propertyTypes",
    links: [
      { label: "footer.apartments", href: "/search?deal=sale&property_type=apartment" },
      { label: "nav.newBuildings", href: "/search?deal=sale&property_type=new_building" },
      { label: "footer.houses", href: "/search?deal=sale&property_type=house" },
      { label: "footer.villas", href: "/search?deal=sale&property_type=villa" },
      { label: "footer.land", href: "/search?deal=sale&property_type=land" },
      { label: "footer.commercial", href: "/search?deal=sale&property_type=commercial" }
    ]
  },
  {
    title: "nav.rent",
    links: [
      { label: "footer.longRent", href: "/search?deal=rent" },
      { label: "footer.dailyRent", href: "/search?deal=daily" },
      { label: "footer.apartmentRent", href: "/search?deal=rent&property_type=apartment" },
      { label: "footer.officeRent", href: "/search?deal=rent&property_type=office" }
    ]
  },
  {
    title: "footer.company",
    links: [
      { label: "footer.about", href: "/about" },
      { label: "action.addListing", href: "/login" },
      { label: "footer.contact", href: "/contact" }
    ]
  },
  {
    title: "footer.info",
    links: [
      { label: "footer.privacy", href: "/privacy" },
      { label: "footer.terms", href: "/terms" }
    ]
  }
];

export function Footer() {
  const { t } = useI18n();
  return (
    <footer className="mt-16 border-t border-border bg-surface">
      <div className="mx-auto max-w-[1440px] px-4 py-12 lg:px-6">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-6">
          <div className="lg:col-span-2">
            <Logo />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              YeniMenzil.az — {t("footer.description")}
            </p>
            <p className="mt-4 text-xs text-foreground/45">
              © {new Date().getFullYear()} YeniMenzil.az. {t("footer.rights")}
            </p>
          </div>
          {FOOTER_COLUMNS.map((column) => (
            <nav key={column.title} aria-label={t(column.title)}>
              <h3 className="text-sm font-semibold text-foreground">
                {t(column.title)}
              </h3>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={link.href + link.label}>
                    <Link
                      href={link.href}
                      className="text-[13.5px] text-muted-foreground transition-colors hover:text-brand"
                    >
                      {t(link.label)}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>
      </div>
    </footer>
  );
}
