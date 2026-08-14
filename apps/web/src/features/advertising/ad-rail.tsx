import Link from "next/link";
import { Megaphone } from "lucide-react";

export interface PublicBanner { id: string; title_az: string; subtitle_az: string; image_url: string | null; link_url: string | null; cta_label_az: string | null; badge_az: string | null; }

export function AdRail({ banner, side }: { banner?: PublicBanner; side: "left" | "right" }) {
  if (banner) return <a href={banner.link_url ?? "/contact"} className="sticky top-24 block overflow-hidden rounded-2xl border border-border bg-surface shadow-sm" aria-label={`${banner.title_az} reklamı`}>
    {banner.image_url ? <img src={banner.image_url} alt={banner.title_az} className="aspect-[1/3] w-full object-cover"/> : <div className="flex aspect-[1/3] flex-col items-center justify-center bg-gradient-to-b from-brand-soft to-surface p-5 text-center"><Megaphone className="h-9 w-9 text-brand"/><strong className="mt-4 text-lg">{banner.title_az}</strong><span className="mt-2 text-sm text-muted-foreground">{banner.subtitle_az}</span><span className="mt-5 rounded-lg bg-brand px-4 py-2 text-sm font-bold text-white">{banner.cta_label_az ?? "Ətraflı"}</span></div>}
  </a>;
  return <Link href="/contact?subject=advertising" className="sticky top-24 flex min-h-[440px] flex-col items-center justify-center rounded-2xl border border-dashed border-brand/30 bg-brand-soft/40 p-5 text-center transition hover:border-brand hover:bg-brand-soft">
    <span className="rounded-full bg-white p-3 text-brand shadow-sm"><Megaphone className="h-6 w-6"/></span><strong className="mt-4">Burada reklam verin</strong><span className="mt-2 text-xs text-muted-foreground">{side === "left" ? "Sol" : "Sağ"} premium reklam sahəsi</span><span className="mt-5 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white">Reklam sifariş et</span>
  </Link>;
}
