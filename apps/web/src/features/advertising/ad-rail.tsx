import Link from "next/link";
import { Megaphone } from "lucide-react";

export interface PublicBanner { id: string; title_az: string; subtitle_az: string; image_url: string | null; link_url: string | null; cta_label_az: string | null; badge_az: string | null; }

export function TopAdBanner({ banner }: { banner?: PublicBanner }) {
  return <div className="mx-auto max-w-[1240px] px-4 pt-4 lg:px-6">
    <a href={banner?.link_url ?? "/contact?subject=top-advertising"} className="group relative block h-[104px] overflow-hidden rounded-2xl border border-border bg-[#071b31] text-white shadow-sm md:h-[128px]" aria-label="Yuxarı reklam sahəsi">
      <img src={banner?.image_url ?? "/ads/bmw-demo-baku.png"} alt={banner?.title_az ?? "BMW demo reklamı"} className="absolute inset-0 h-full w-full object-cover object-[center_67%] transition duration-500 group-hover:scale-[1.02]" />
      <div className="absolute inset-0 bg-gradient-to-r from-[#041426]/95 via-[#041426]/65 to-transparent" />
      <div className="relative flex h-full max-w-md flex-col justify-center px-6 md:px-10"><span className="text-[9px] font-bold uppercase tracking-[0.2em] text-white/60">{banner?.badge_az ?? "Demo reklam"}</span><strong className="mt-1 text-xl md:text-2xl">{banner?.title_az ?? "BMW ilə yeni üfüqlərə"}</strong><span className="mt-1 text-xs text-white/75 md:text-sm">{banner?.subtitle_az ?? "Premium hərəkət. Premium ünvan."}</span></div>
      <span className="absolute bottom-4 right-5 rounded-lg bg-white px-4 py-2 text-xs font-bold text-[#071b31] md:bottom-auto md:right-8 md:top-1/2 md:-translate-y-1/2">{banner?.cta_label_az ?? "Ətraflı bax"}</span>
    </a>
  </div>;
}

export function AdRail({ banner, side }: { banner?: PublicBanner; side: "left" | "right" }) {
  if (banner && side === "right") return <a href={banner.link_url ?? "/contact"} className="sticky top-20 block min-h-[calc(100vh-6rem)] overflow-hidden rounded-2xl border border-border bg-surface shadow-sm" aria-label={`${banner.title_az} reklamı`}>
    {banner.image_url ? <img src={banner.image_url} alt={banner.title_az} className="absolute inset-0 h-full w-full object-cover"/> : <div className="flex min-h-[calc(100vh-6rem)] flex-col items-center justify-center bg-gradient-to-b from-brand-soft to-surface p-5 text-center"><Megaphone className="h-9 w-9 text-brand"/><strong className="mt-4 text-lg">{banner.title_az}</strong><span className="mt-2 text-sm text-muted-foreground">{banner.subtitle_az}</span><span className="mt-5 rounded-lg bg-brand px-4 py-2 text-sm font-bold text-white">{banner.cta_label_az ?? "Ətraflı"}</span></div>}
  </a>;
  if (side === "left") return <Link href="/contact?subject=BMW%20demo%20reklam" className="sticky top-20 block overflow-hidden rounded-2xl border border-border bg-[#071b31] text-white shadow-sm" aria-label="BMW demo reklamı">
    <div className="relative min-h-[calc(100vh-6rem)]">
      <img src="/ads/bmw-demo-baku.png" alt="Bakıda premium sedan — demo reklam" className="absolute inset-0 h-full w-full object-cover" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#041426]/95 via-transparent to-[#041426]/80" />
      <div className="absolute inset-x-0 top-0 p-4 text-center"><span className="text-[9px] font-semibold uppercase tracking-[0.22em] text-white/60">Demo reklam</span><strong className="mt-2 block text-xl tracking-tight">BMW</strong><span className="mt-1 block text-[11px] text-white/75">Hərəkətin yeni ünvanı</span></div>
      <span className="absolute bottom-4 left-3 right-3 rounded-lg bg-white px-3 py-2 text-center text-xs font-bold text-[#071b31]">Ətraflı bax</span>
    </div>
  </Link>;
  return <Link href="/contact?subject=advertising" className="sticky top-20 flex min-h-[calc(100vh-6rem)] flex-col items-center justify-center rounded-2xl border border-dashed border-brand/30 bg-brand-soft/40 p-5 text-center transition hover:border-brand hover:bg-brand-soft">
    <span className="rounded-full bg-white p-3 text-brand shadow-sm"><Megaphone className="h-6 w-6"/></span><strong className="mt-4">Burada reklam verin</strong><span className="mt-2 text-xs text-muted-foreground">Sağ premium reklam sahəsi</span><span className="mt-5 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white">Reklam sifariş et</span>
  </Link>;
}
