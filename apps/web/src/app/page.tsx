import Link from "next/link";
import { SectionHeading } from "@yenimenzil/ui";
import { HomeTopBanner } from "@/components/ads/home-top-banner";
import { Header } from "@/components/layout/header";
import { fetchFeaturedSections } from "@/services/property-api";
import { fetchComplexes } from "@/services/complex-api";
import { PropertyGrid } from "@/features/properties/property-grid";
import { AdSlot } from "@/components/ads/ad-slot";
import { getPopularAreas } from "@/data/areas";
import { POPULAR_PLACES } from "@/data/locations";
import HeroSection from "@/components/HeroSection";
import { Suspense } from "react";
import { MapView } from "@/features/map/map-view";
import { formatPriceShort } from "@/lib/format";

export const dynamic = 'force-dynamic';

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

  const featuredListings = sections.premium.slice(0, 8);
  const newListings = sections.newest.slice(0, 8);
  const premiumListings = sections.premium.slice(0, 8);
  const discountedListings = sections.priceDropped.slice(0, 8);
  const newBuildings = sections.newBuildings.slice(0, 8);

  const mapMarkers = all
    .filter((p) => p.location.point.lat && p.location.point.lng)
    .slice(0, 200)
    .map((p) => ({
      id: p.id,
      price: p.price,
      formattedPrice: formatPriceShort(p.price),
      point: p.location.point
    }));

  return (
    <div data-homepage-version="idealev-v5" className="relative overflow-x-hidden min-h-screen">
      <HomeTopBanner />
      <Header />
      <main className="relative grid grid-cols-[minmax(0,1fr)_minmax(0,1240px)_minmax(0,1fr)] gap-0">
        <aside className="col-span-1 bg-blue-50 border-r border-gray-200 hidden lg:block">
          <AdSlot placement="LEFT_RAIL" className="w-full h-full object-cover" />
        </aside>
        <div className="col-span-1 lg:col-span-1 min-h-[calc(100dvh-11rem)] p-4">
          <Suspense fallback={<div className="h-64 flex items-center justify-center">Loading...</div>}>
            <HeroSection />
          </Suspense>

          <section aria-labelledby="categories-title" className="mb-6">
            <h2 id="categories-title" className="text-xl font-semibold text-foreground mb-4">Elan növü</h2>
            <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
              <a href="/search?deal=sale&property_type=new_building" className="rounded-xl bg-surface px-3 py-4 text-center">Yeni tikili</a>
              <a href="/search?deal=sale&property_type=old_building" className="rounded-xl bg-surface px-3 py-4 text-center">Köhnə tikili</a>
              <a href="/search?deal=sale&property_type=house" className="rounded-xl bg-surface px-3 py-4 text-center">Həyət evi / Bağ evi</a>
              <a href="/search?deal=sale&property_type=office" className="rounded-xl bg-surface px-3 py-4 text-center">Ofis</a>
              <a href="/search?deal=sale&property_type=garage" className="rounded-xl bg-surface px-3 py-4 text-center">Qaraj</a>
              <a href="/search?deal=sale&property_type=land" className="rounded-xl bg-surface px-3 py-4 text-center">Torpaq</a>
              <a href="/search?deal=sale&property_type=commercial" className="rounded-xl bg-surface px-3 py-4 text-center">Obyekt</a>
            </div>
          </section>

          <section aria-labelledby="popular-locations-title" className="mb-6">
            <h2 id="popular-locations-title" className="text-xl font-semibold text-foreground mb-3">Populyar ərazi</h2>
            <div className="flex flex-wrap gap-2">
              {POPULAR_PLACES.slice(0, 12).map((place) => (
                <Link
                  key={place.label}
                  href={`/search?deal=sale&district=${place.district.toLowerCase().replace(/\s+/g, '-')}`}
                  className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3.5 py-1.5 text-[13px] font-medium text-foreground/70 shadow-sm hover:border-brand/40 hover:text-brand transition-colors"
                >
                  {place.label}
                </Link>
              ))}
            </div>
          </section>

          <section aria-labelledby="stats-title" className="mb-8">
            <h2 id="stats-title" className="sr-only">Platform statistikası</h2>
            <div className="grid grid-cols-3 gap-4 md:grid-cols-3">
              {stats.map((stat) => (
                <div key={stat.label} className="text-center rounded-xl bg-surface p-4 border border-border/50">
                  <div className="text-2xl md:text-3xl font-bold text-brand">{stat.value}</div>
                  <div className="text-[12px] text-muted-foreground mt-1">{stat.label}</div>
                </div>
              ))}
            </div>
          </section>

          {featuredListings.length > 0 && (
            <section aria-labelledby="featured-listings-title" className="mb-8">
              <SectionHeading
                title="Seçilmiş elanlar"
                subtitle="Müəyyən edilmiş premium elanlar"
                linkHref="/search?sort=premium"
                linkLabel="Hamısına bax"
              />
              <PropertyGrid listings={featuredListings} columns={4} />
            </section>
          )}

          {newListings.length > 0 && (
            <section aria-labelledby="new-listings-title" className="mb-8">
              <SectionHeading
                title="Yeni elanlar"
                subtitle="Son əlavə olunan elanlar"
                linkHref="/search?sort=newest"
                linkLabel="Hamısına bax"
              />
              <PropertyGrid listings={newListings} columns={4} />
            </section>
          )}

          {premiumListings.length > 0 && (
            <section aria-labelledby="premium-listings-title" className="mb-8">
              <SectionHeading
                title="Premium elanlar"
                subtitle="Yüksək keyfiyyətli, yoxlanılmış elanlar"
                linkHref="/search?premium=true"
                linkLabel="Hamısına bax"
              />
              <PropertyGrid listings={premiumListings} columns={4} />
            </section>
          )}

          {discountedListings.length > 0 && (
            <section aria-labelledby="discounted-listings-title" className="mb-8">
              <SectionHeading
                title="Endirimli elanlar"
                subtitle="Qiyməti endirilmiş elanlar"
                linkHref="/search?price_drop=true"
                linkLabel="Hamısına bax"
              />
              <PropertyGrid listings={discountedListings} columns={4} />
            </section>
          )}

          {newBuildings.length > 0 && (
            <section aria-labelledby="new-buildings-title" className="mb-8">
              <SectionHeading
                title="Yeni tikililər"
                subtitle="Yenidən tikilən binalardakı mənzillər"
                linkHref="/search?deal=sale&property_type=new_building"
                linkLabel="Hamısına bax"
              />
              <PropertyGrid listings={newBuildings} columns={4} />
            </section>
          )}

          <section aria-labelledby="residential-complexes-title" className="mb-8">
            <SectionHeading
              title="Yaşayış kompleksləri"
              subtitle="Müasir yaşayış komplekslərində mənzillər"
              linkHref="/complexes"
              linkLabel="Hamısına bax"
            />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {complexes.slice(0, 4).map((complex) => (
                <Link
                  key={complex.id}
                  href={`/complexes/${complex.slug}`}
                  className="group rounded-xl overflow-hidden bg-surface border border-border/50 transition-all hover:border-brand/40 hover:shadow-lg"
                >
                  <div
                    className="aspect-[4/3] bg-gray-100 relative overflow-hidden"
                    style={complex.coverImage ? { backgroundImage: `url(${complex.coverImage})`, backgroundSize: 'cover', backgroundPosition: 'center' } : undefined}
                  >
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                    <div className="absolute bottom-3 left-3 right-3 text-white">
                      <p className="text-xs text-white/70">{complex.district ?? complex.city ?? ''}</p>
                      <h3 className="font-semibold text-lg">{complex.name}</h3>
                    </div>
                  </div>
                  <div className="p-4">
                    <p className="text-sm text-muted-foreground">{complex.propertiesCount ?? complex.totalUnits ?? 0} məkan</p>
                  </div>
                </Link>
              ))}
            </div>
          </section>

          <section aria-labelledby="benefits-title" className="mb-8 border-t border-border/50 pt-8">
            <h2 id="benefits-title" className="text-xl font-semibold text-foreground mb-6 text-center">Nə üçün IdealEv?</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="px-4 py-5 bg-surface rounded-xl border border-border/70 text-center">
                <div className="text-brand text-2xl mb-2">Pulsuz elan yerləşdir</div>
                <div className="text-[13px] text-muted-foreground">Heç bir ödənişsiz elanlarınızı yayınlayın</div>
              </div>
              <div className="px-4 py-5 bg-surface rounded-xl border border-border/70 text-center">
                <div className="text-brand text-2xl mb-2">Geniş аудитория</div>
                <div className="text-[13px] text-muted-foreground">Aylıq minlərlə potensial alıcılarla tanış olun</div>
              </div>
              <div className="px-4 py-5 bg-surface rounded-xl border border-border/70 text-center">
                <div className="text-brand text-2xl mb-2">Təhlükəsiz ödəniş</div>
                <div className="text-[13px] text-muted-foreground">Qorunan əməliyyatlar, hər iki tərəf qorunur</div>
              </div>
              <div className="px-4 py-5 bg-surface rounded-xl border border-border/70 text-center">
                <div className="text-brand text-2xl mb-2">24/7 Dəstək</div>
                <div className="text-[13px] text-muted-foreground">Hər zaman sizləyik, real-time kömək</div>
              </div>
            </div>
          </section>

          <section aria-labelledby="map-title" className="mb-8">
            <SectionHeading
              title="Xəritədə axtar"
              subtitle="Məkanlara görə elanları xəritə üzərindən kəşf edin"
              linkHref="/map"
              linkLabel="Xəritəni aç"
              align="center"
            />
            <div className="rounded-2xl overflow-hidden border border-border/50 bg-surface" style={{ height: "480px" }}>
              <MapView
                markers={mapMarkers}
                center={{ lat: 40.4093, lng: 49.8671 }}
                zoom={10}
                showBoundsSearch
                searchLabel="Bu bölgədə axtar"
              />
            </div>
          </section>
        </div>
        <aside className="col-span-1 bg-red-50 border-l border-gray-200 hidden lg:block">
          <AdSlot placement="RIGHT_RAIL" className="w-full h-full object-cover" />
        </aside>
      </main>
    </div>
  );
}