import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Building2 } from "lucide-react";
import { SectionHeading } from "@yenimenzil/ui";
import { fetchFeaturedSections } from "@/services/property-api";
import { fetchComplexes } from "@/services/complex-api";
import { SearchBar } from "@/features/search/search-bar";
import { PropertyGrid } from "@/features/properties/property-grid";
import { MapDiscover } from "@/features/map/map-discover";
import { AdSlot } from "@/components/ads/ad-slot";
import { getPopularAreas } from "@/data/areas";

export const metadata: Metadata = {
  title: "YeniMenzil.az — Yeni məkanını burada tap"
};

export default async function HomePage() {
  const sections = await fetchFeaturedSections();
  const complexes = await fetchComplexes();
  const all = sections.all;
  const activeCount = all.filter((p) => p.status === "active").length;
  const droppedCount = all.filter(
    (p) =>
      p.priceHistory.length >= 2 &&
      p.priceHistory.at(-1)!.price < p.priceHistory[0]!.price
  ).length;
  const popularAreas = getPopularAreas(all);

  const stats = [
    { value: `${activeCount}+`, label: "aktiv elan" },
    { value: String(popularAreas.length), label: "populyar ərazi" },
    { value: String(droppedCount), label: "qiyməti endirilmiş elan" }
  ];

  return (
    <div>
      <section className="border-b border-border/70 bg-background">
        <div className="mx-auto max-w-[1440px] px-4 pb-7 pt-7 md:pt-10 lg:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-[30px] font-semibold leading-tight tracking-tight text-foreground md:text-[42px]">
              Yeni məkanını{" "}
              <span className="text-brand">burada</span> tap.
            </h1>
            <p className="mx-auto mt-2.5 max-w-xl text-[14px] leading-relaxed text-muted-foreground md:text-[15px]">
              Azərbaycan üzrə mənzil, villa, torpaq, obyekt və digər daşınmaz
              əmlak elanlarını rahat şəkildə kəşf et.
            </p>
          </div>
          <div className="mx-auto mt-6 max-w-4xl">
            <SearchBar />
          </div>
          <AdSlot placement="HOME_TOP_BANNER" />
          <dl className="mx-auto mt-6 flex max-w-lg items-center justify-center gap-6 text-center md:gap-10">
            {stats.map((stat) => (
              <div key={stat.label} className="flex flex-col-reverse">
                <dt className="text-[11px] text-muted-foreground sm:text-xs">
                  {stat.label}
                </dt>
                <dd className="text-lg font-semibold tracking-tight text-foreground sm:text-xl">
                  {stat.value}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <div className="mx-auto max-w-[1440px] space-y-12 px-4 pt-8 md:space-y-14 lg:px-6">
        <section aria-labelledby="new-listings-title">
          <SectionHeading
            title="Yeni elanlar"
            subtitle="Son əlavə olunan elanlar"
            linkHref="/search?sort=newest"
            linkLabel="Hamısına bax"
          />
          <PropertyGrid listings={sections.newest.slice(0, 8)} columns={4} />
        </section>

        <AdSlot placement="HOME_MIDDLE_BANNER" />

        <MapDiscover />

        <section aria-labelledby="premium-listings-title">
          <div className="mb-5 flex items-end justify-between gap-4">
            <div>
              <h2
                id="premium-listings-title"
                className="flex items-center gap-2 text-lg font-semibold tracking-tight text-foreground sm:text-2xl"
              >
                Premium elanlar
                <span className="rounded-full bg-[#F5EBD8] px-2 py-0.5 text-[11px] font-semibold text-[#8a6a2f]">
                  VIP
                </span>
              </h2>
              <p className="mt-0.5 text-[13px] text-muted-foreground sm:text-sm">
                Seçilmiş yüksək keyfiyyətli daşınmaz əmlak
              </p>
            </div>
            <Link
              href="/search?deal=sale"
              className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-brand/20 bg-brand-soft/60 px-4 py-2 text-[13px] font-semibold text-brand shadow-sm transition-all hover:-translate-y-px hover:border-brand/40 hover:bg-brand-soft"
            >
              Hamısına bax
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
          <PropertyGrid listings={sections.premium.slice(0, 4)} columns={4} />
        </section>

        <section aria-labelledby="price-drop-title">
          <SectionHeading
            title="Qiyməti endirilənlər"
            subtitle="Satıcılar qiyməti endirib"
            linkHref="/search?sort=newest"
            linkLabel="Hamısına bax"
          />
          <PropertyGrid listings={sections.priceDropped.slice(0, 4)} columns={4} />
        </section>

        <section aria-labelledby="new-buildings-title">
          <SectionHeading
            title="Yeni tikililər"
            subtitle="Müasir tikinti, təhvil verilən binalar"
            linkHref="/search?deal=sale&property_type=new_building"
            linkLabel="Hamısına bax"
          />
          <PropertyGrid listings={sections.newBuildings.slice(0, 4)} columns={4} />
        </section>

        {complexes.length > 0 && (
          <section aria-labelledby="complexes-title">
            <SectionHeading
              title="Yaşayış kompleksləri"
              subtitle="Tikinti şirkətlərinin təqdimatı"
            />
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
              {complexes.slice(0, 6).map((complex) => (
                <Link
                  key={complex.id}
                  href={`/complexes/${complex.id}`}
                  className="group flex items-center gap-3 rounded-2xl bg-surface px-4 py-4 ring-1 ring-border/70 transition-all hover:-translate-y-0.5 hover:shadow-card hover:ring-brand/25"
                >
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-soft text-brand transition-colors group-hover:bg-brand group-hover:text-white">
                    <Building2 className="h-5 w-5" />
                  </span>
                  <span>
                    <span className="block text-sm font-semibold text-foreground">
                      {complex.name}
                    </span>
                    <span className="block text-xs text-muted-foreground">
                      {complex.propertiesCount} elan
                      {complex.developerName ? ` · ${complex.developerName}` : ""}
                    </span>
                  </span>
                  <ArrowRight className="ml-auto h-4 w-4 text-foreground/25 transition-colors group-hover:text-brand" />
                </Link>
              ))}
            </div>
          </section>
        )}

        <section aria-labelledby="popular-areas-title">
          <SectionHeading
            title="Populyar ərazilər"
            subtitle="Ən çox baxılan rayon və qəsəbələr"
          />
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
            {popularAreas.map((area) => (
              <Link
                key={area.name}
                href={area.href}
                className="group flex items-center gap-3 rounded-2xl bg-surface px-4 py-4 ring-1 ring-border/70 transition-all hover:-translate-y-0.5 hover:shadow-card hover:ring-brand/25"
              >
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-soft text-brand transition-colors group-hover:bg-brand group-hover:text-white">
                  <Building2 className="h-5 w-5" />
                </span>
                <span>
                  <span className="block text-sm font-semibold text-foreground">
                    {area.name}
                  </span>
                  <span className="block text-xs text-muted-foreground">
                    {area.count} elan
                  </span>
                </span>
                <ArrowRight className="ml-auto h-4 w-4 text-foreground/25 transition-colors group-hover:text-brand" />
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
