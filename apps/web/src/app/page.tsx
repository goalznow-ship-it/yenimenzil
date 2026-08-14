import Link from "next/link";
import { ArrowRight, Building2, ShieldCheck } from "lucide-react";
import { SectionHeading } from "@yenimenzil/ui";
import { fetchFeaturedSections } from "@/services/property-api";
import { SearchBar } from "@/features/search/search-bar";
import { PropertyGrid } from "@/features/properties/property-grid";
import { MapDiscover } from "@/features/map/map-discover";
import { getPopularAreas } from "@/data/areas";
import { getTranslations } from "@/lib/i18n-server";
import { fetchComplexes } from "@/services/development-api";
import { ComplexCard } from "@/features/developments/complex-card";
import { fetchPublicBanners } from "@/services/platform-api";
import { AdRail } from "@/features/advertising/ad-rail";
import { fetchAgencyDirectory } from "@/services/agency-directory-api";

export default async function HomePage() {
  const { t } = await getTranslations();
  const sections = await fetchFeaturedSections();
  const [complexes, banners, agencies] = await Promise.all([
    fetchComplexes().catch(() => []),
    fetchPublicBanners(),
    fetchAgencyDirectory()
  ]);
  const all = sections.all;
  const activeCount = all.filter((p) => p.status === "active").length;
  const droppedCount = all.filter(
    (p) =>
      p.priceHistory.length >= 2 &&
      p.priceHistory.at(-1)!.price < p.priceHistory[0]!.price
  ).length;
  const popularAreas = getPopularAreas(all);
  const stats = [
    { value: `${activeCount}+`, label: t("home.active") },
    { value: String(popularAreas.length), label: t("home.popularArea") },
    { value: String(droppedCount), label: t("home.priceDropStat") }
  ];

  return (
    <div>
      <section className="border-b border-border/70 bg-background">
        <div className="mx-auto max-w-[1440px] px-4 pb-7 pt-7 md:pt-10 lg:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-[30px] font-semibold leading-tight tracking-tight text-foreground md:text-[42px]">
              {t("home.title.before")}{" "}
              <span className="text-brand">{t("home.title.highlight")}</span>{" "}{t("home.title.after")}
            </h1>
            <p className="mx-auto mt-2.5 max-w-xl text-[14px] leading-relaxed text-muted-foreground md:text-[15px]">
              {t("home.subtitle")}
            </p>
          </div>
          <div className="mx-auto mt-6 max-w-[1240px]">
            <SearchBar />
          </div>
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

      <div className="mx-auto grid max-w-[1536px] gap-5 px-4 pt-7 lg:px-5 xl:grid-cols-[140px_minmax(0,1fr)_140px]">
        <aside className="hidden xl:block"><AdRail banner={banners[0]} side="left" /></aside>
        <div className="min-w-0 space-y-12 md:space-y-14">
        <section aria-labelledby="complexes-title">
          <SectionHeading title="Yaşayış kompleksləri" subtitle="Birbaşa developer təklifləri" linkHref="/residential-complexes" linkLabel={t("action.viewAll")} />
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{complexes.slice(0, 3).map((item) => <ComplexCard key={item.id} item={item} />)}</div>
        </section>

        {agencies.length > 0 ? <section aria-labelledby="agencies-title">
          <SectionHeading title="Agentliklər" subtitle="Təsdiqlənmiş əmlak mütəxəssisləri" linkHref="/agencies" linkLabel="Bütün agentliklər" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{agencies.slice(0,4).map((agency) => <Link key={agency.id} href={`/agencies/${agency.id}`} className="group rounded-2xl border border-border bg-surface p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-card"><div className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-2xl bg-brand-soft text-brand">{agency.logo_url ? <img src={agency.logo_url} alt={agency.name} className="h-full w-full object-cover"/> : <Building2 className="h-8 w-8"/>}</div><p className="mt-4 flex items-center gap-1 font-semibold">{agency.name}{agency.is_verified && <ShieldCheck className="h-4 w-4 text-brand"/>}</p><p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{agency.description ?? "Daşınmaz əmlak agentliyi"}</p></Link>)}</div>
        </section> : null}

        <section aria-labelledby="new-listings-title">
          <SectionHeading
            title={t("home.new")}
            subtitle={t("home.newSubtitle")}
            linkHref="/search?sort=newest"
            linkLabel={t("action.viewAll")}
          />
          <PropertyGrid listings={sections.newest.slice(0, 8)} columns={4} />
        </section>

        <MapDiscover />

        <section aria-labelledby="premium-listings-title">
          <div className="mb-5 flex items-end justify-between gap-4">
            <div>
              <h2
                id="premium-listings-title"
                className="flex items-center gap-2 text-lg font-semibold tracking-tight text-foreground sm:text-2xl"
              >
                {t("home.premium")}
                <span className="rounded-full bg-[#F5EBD8] px-2 py-0.5 text-[11px] font-semibold text-[#8a6a2f]">
                  VIP
                </span>
              </h2>
              <p className="mt-0.5 text-[13px] text-muted-foreground sm:text-sm">
                {t("home.premiumSubtitle")}
              </p>
            </div>
            <Link
              href="/search?deal=sale"
              className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-brand/20 bg-brand-soft/60 px-4 py-2 text-[13px] font-semibold text-brand shadow-sm transition-all hover:-translate-y-px hover:border-brand/40 hover:bg-brand-soft"
            >
              {t("action.viewAll")}
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
          <PropertyGrid listings={sections.premium.slice(0, 4)} columns={4} />
        </section>

        <section aria-labelledby="price-drop-title">
          <SectionHeading
            title={t("home.priceDrops")}
            subtitle={t("home.priceDropsSubtitle")}
            linkHref="/search?sort=newest"
            linkLabel={t("action.viewAll")}
          />
          <PropertyGrid listings={sections.priceDropped.slice(0, 4)} columns={4} />
        </section>

        <section aria-labelledby="new-buildings-title">
          <SectionHeading
            title={t("home.newBuildings")}
            subtitle={t("home.newBuildingsSubtitle")}
            linkHref="/search?deal=sale&property_type=new_building"
            linkLabel={t("action.viewAll")}
          />
          <PropertyGrid listings={sections.newBuildings.slice(0, 4)} columns={4} />
        </section>

        <section aria-labelledby="popular-areas-title">
          <SectionHeading
            title={t("home.popularAreas")}
            subtitle={t("home.popularAreasSubtitle")}
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
                    {area.count} {t("listing.count")}
                  </span>
                </span>
                <ArrowRight className="ml-auto h-4 w-4 text-foreground/25 transition-colors group-hover:text-brand" />
              </Link>
            ))}
          </div>
        </section>
        </div>
        <aside className="hidden xl:block"><AdRail banner={banners[1]} side="right" /></aside>
      </div>
    </div>
  );
}
