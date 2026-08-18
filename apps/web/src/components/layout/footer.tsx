import Link from "next/link";
import { Logo } from "./logo";

const FOOTER_COLUMNS = [
  {
    title: "Əmlak növləri",
    links: [
      { label: "Mənzillər", href: "/search?deal=sale&property_type=apartment" },
      { label: "Yeni tikililər", href: "/search?deal=sale&property_type=new_building" },
      { label: "Həyət evləri", href: "/search?deal=sale&property_type=house" },
      { label: "Villalar", href: "/search?deal=sale&property_type=villa" },
      { label: "Torpaq sahələri", href: "/search?deal=sale&property_type=land" },
      { label: "Kommersiya obyektləri", href: "/search?deal=sale&property_type=commercial" }
    ]
  },
  {
    title: "Kirayə",
    links: [
      { label: "Uzunmüddətli kirayə", href: "/search?deal=rent" },
      { label: "Günlük kirayə", href: "/search?deal=daily" },
      { label: "Mənzil kirayə", href: "/search?deal=rent&property_type=apartment" },
      { label: "Ofis kirayə", href: "/search?deal=rent&property_type=office" }
    ]
  },
  {
    title: "Şirkət",
    links: [
      { label: "Haqqımızda", href: "/about" },
      { label: "Elan yerləşdir", href: "/login" },
      { label: "Əlaqə", href: "/contact" }
    ]
  },
  {
    title: "Məlumat",
    links: [
      { label: "Gizlilik siyasəti", href: "/privacy" },
      { label: "İstifadəçi razılaşması", href: "/terms" }
    ]
  }
];

export function Footer() {
  return (
    <footer className="mt-16 border-t border-border bg-surface">
      <div className="mx-auto max-w-[1440px] px-4 py-12 lg:px-6">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-6">
          <div className="lg:col-span-2">
            <Logo />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              IdealEv.az — Azərbaycan üzrə daşınmaz əmlak elanları üçün
              müasir platforma. Yeni məkanını burada tap.
            </p>
            <p className="mt-4 text-xs text-foreground/45">
              © {new Date().getFullYear()} IdealEv.az. Bütün hüquqlar
              qorunur.
            </p>
          </div>
          {FOOTER_COLUMNS.map((column) => (
            <nav key={column.title} aria-label={column.title}>
              <h3 className="text-sm font-semibold text-foreground">
                {column.title}
              </h3>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={link.href + link.label}>
                    <Link
                      href={link.href}
                      className="text-[13.5px] text-muted-foreground transition-colors hover:text-brand"
                    >
                      {link.label}
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
