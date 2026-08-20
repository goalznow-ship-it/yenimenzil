import Link from "next/link";
import { SectionHeading } from "@yenimenzil/ui";
import { fetchFeaturedSections } from "@/services/property-api";
import { PropertyGrid } from "@/features/properties/property-grid";
import { AdSlot } from "@/components/ads/ad-slot";
import { getPopularAreas } from "@/data/areas";
import { POPULAR_PLACES } from "@/data/locations";
import HeroSection from "@/components/HeroSection";
import { Suspense } from "react";
import { MapView } from "@/features/map/map-view";
import { formatPriceShort } from "@/lib/format";
import {
  Building2,
  Building,
  Home,
  Briefcase,
  Warehouse,
  Grid,
  Store,
} from "lucide-react";

export default async function HomePage() {
  const sections = await fetchFeaturedSections();
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

  const mapMarkers = all.slice(0, 4).map((listing) => ({
    id: listing.id.toString(),
    point: listing.location.point,
    price: listing.price,
    formattedPrice: formatPriceShort(listing.price),
    image: listing.images[0]?.src,
    title: listing.title,
    address: listing.location.addressText
  }));

  const featuredListings = sections.newest.slice(0, 8);
  const newListings = sections.newest.slice(0, 12);
  const premiumListings = sections.premium.slice(0, 8);
  const priceDroppedListings = sections.priceDropped.slice(0, 8);
  const newBuildings = sections.newBuildings.slice(0, 8);

  return (
    <div data-homepage-version="idealev-v5" className="relative overflow-x-hidden min-h-screen">
      {/* HEADER + MAIN CONTENT */}
      <div className="relative">
        {/* LEFT FULL RAIL - Flush against viewport edge */}
        <aside
          className="hidden xl:block fixed left-0 top-[228px] bottom-0 w-[120px] z-20 pointer-events-none"
        >
          <AdSlot
            placement="LEFT_RAIL"
            className="w-full h-[600px] max-w-[120px]"
          />
        </aside>

        {/* MAIN CONTENT - centered */}
        <main className="mx-auto relative pt-4 max-w-[1240px] px-4">
          <Suspense fallback={<div className="h-64 flex items-center justify-center text-muted-foreground">Loading...</div>}>
            <HeroSection />
          </Suspense>

          {/* CATEGORY SHORTCUTS - Polished Premium Row */}
          <section aria-labelledby="categories-title" className="mb-4">
            <div className="flex items-center justify-between mb-3">
              <h2 id="categories-title" className="text-xl font-semibold text-foreground">
                Elan növü
              </h2>
            </div>
            <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
              {[
                { label: "Yeni tikili", href: "/search?deal=sale&property_type=new_building", icon: Building2 },
                { label: "Köhnə tikili", href: "/search?deal=sale&property_type=old_building", icon: Building },
                { label: "Həyət evi / Bağ evi", href: "/search?deal=sale&property_type=house", icon: Home },
                { label: "Ofis", href: "/search?deal=sale&property_type=office", icon: Briefcase },
                { label: "Qaraj", href: "/search?deal=sale&property_type=garage", icon: Warehouse },
                { label: "Torpaq", href: "/search?deal=sale&property_type=land", icon: Grid },
                { label: "Obyekt", href: "/search?deal=sale&property_type=commercial", icon: Store },
              ].map(({ label, href, icon: Icon }) => (
                <Link
                  key={label}
                  href={href}
                  className="group flex flex-col items-center justify-center gap-2.5 rounded-xl bg-surface px-3 py-4 border border-border/50 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md hover:border-brand/30 hover:bg-brand/5 text-center min-h-[110px]"
                >
                  <div className="flex h-14 w-14 items-center justify-center rounded-lg bg-brand-soft text-brand transition-colors group-hover:bg-brand group-hover:text-white shadow-sm">
                    <Icon className="h-7 w-7" />
                  </div>
                  <span className="text-xs font-medium text-foreground group-hover:text-brand leading-tight">
                    {label}
                  </span>
                </Link>
              ))}
            </div>
          </section>

          {/* POPULAR LOCATIONS - Polished Chip Row */}
          <section aria-labelledby="popular-locations-title" className="mb-4">
            <h2 id="popular-locations-title" className="text-xl font-semibold text-foreground mb-3">
              Populyar ərazilər
            </h2>
            <div className="flex flex-wrap gap-2">
              {POPULAR_PLACES.slice(0, 12).map((place) => (
                <Link
                  key={place.label}
                  href={`/search?deal=sale&district=${place.label.toLowerCase().replace(/\s+/g, '-')}`}
                  className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3.5 py-1.5 text-[13px] font-medium text-foreground/70 shadow-sm transition-all hover:-translate-y-0.5 hover:border-brand/40 hover:text-brand hover:bg-brand/5"
                >
                  <span className="relative flex h-4 w-4 items-center justify-center">
                    <svg className="h-3 w-3 text-brand/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </span>
                  {place.label}
                </Link>
              ))}
            </div>
          </section>

          {/* SEÇİLMİŞ ELANLAR - Featured Listings */}
          <section aria-labelledby="featured-listings-title" className="mb-6">
            <SectionHeading
              title="Seçilmiş elanlar"
              subtitle="Ən yaxşı təkliflər"
              linkHref="/search?sort=newest"
              linkLabel="Hamısına bax"
            />
            <PropertyGrid listings={featuredListings} columns={4} />
          </section>

          {/* YENİ ELANLAR - New Listings Section */}
          <section aria-labelledby="new-listings-title" className="mb-8">
            <SectionHeading
              title="Yeni elanlar"
              subtitle="Son əlavə olunanlar"
              linkHref="/search?sort=newest"
              linkLabel="Hamısına bax"
            />
            <PropertyGrid listings={newListings} columns={4} />
          </section>

          {/* PREMIUM ELANLAR - VIP/Premium Listings */}
          <section aria-labelledby="premium-listings-title" className="mb-8">
            <SectionHeading
              title="Premium elanlar"
              subtitle="Yüksək keyfiyyətli, yoxlanılmış təkliflər"
              linkHref="/search?deal=sale&is_premium=true"
              linkLabel="Hamısına bax"
            />
            <PropertyGrid listings={premiumListings} columns={4} />
          </section>

          {/* QİYMƏTİ ENDİRİLMİŞ ELANLAR - Price Dropped */}
          <section aria-labelledby="price-dropped-title" className="mb-8">
            <SectionHeading
              title="Qiyməti endirilənlər"
              subtitle="Satıcılar qiyməti endirib"
              linkHref="/search?sort=price_drop"
              linkLabel="Hamısına bax"
            />
            <PropertyGrid listings={priceDroppedListings} columns={4} />
          </section>

          {/* YENİ TİKİLİLƏR - New Buildings */}
          <section aria-labelledby="new-buildings-title" className="mb-12">
            <SectionHeading
              title="Yeni tikililər"
              subtitle="Müasir komplekslər, təhvil verilən binalar"
              linkHref="/search?deal=sale&property_type=new_building"
              linkLabel="Hamısına bax"
            />
            <PropertyGrid listings={newBuildings} columns={4} />
          </section>

          {/* PLATFORM STATISTIKASI - Compact Row (moved lower) */}
          <section aria-labelledby="stats-title" className="mb-12">
            <h2 id="stats-title" className="text-xl font-semibold text-foreground mb-4">
              Platform statistikası
            </h2>
            <div className="grid grid-cols-3 gap-3">
              {stats.map((stat) => (
                <div
                  key={stat.label}
                  className="relative rounded-xl bg-surface p-4 border border-border/50 text-center transition-all hover:border-brand/30 hover:shadow-sm"
                >
                  <div className="text-3xl font-bold text-brand tracking-tight">{stat.value}</div>
                  <div className="text-sm text-muted-foreground mt-1 font-medium">{stat.label}</div>
                </div>
              ))}
            </div>
          </section>

          {/* YAŞAYIŞ KOMPLEKSLƏRİ - Residential Complexes */}
          <section aria-labelledby="complexes-title" className="mb-12">
            <SectionHeading
              title="Yaşayış kompleksləri"
              subtitle="Tikinti şirkətlərinin layihələri"
              linkHref="/complexes"
              linkLabel="Hamısına bax"
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                {
                  name: "Sea Breeze",
                  location: "Xəzər, Buzovna",
                  properties: "247 elan",
                  image: "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=800&q=80",
                  developer: "Azərqat İnşaat",
                  badge: "Sahil yaxınlığı"
                },
                {
                  name: "White City",
                  location: "Yasamal, Bakı",
                  properties: "189 elan",
                  image: "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=800&q=80",
                  developer: "White City MMC",
                  badge: "Metro yaxınlığı"
                },
                {
                  name: "Azərbaycanca",
                  location: "Xəzər, Mərdəkan",
                  properties: "156 elan",
                  image: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80",
                  developer: "Azərbaycanca MMC",
                  badge: "Yeni layihə"
                }
              ].map((complex) => (
                <Link
                  key={complex.name}
                  href="/complexes"
                  className="group block overflow-hidden rounded-xl bg-surface border border-border/50 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:border-brand/30"
                >
                  <div className="relative aspect-[16/9] overflow-hidden">
                    <img
                      src={complex.image}
                      alt={complex.name}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
                    <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
                      <span className="text-xs font-medium bg-brand/90 text-white px-2 py-1 rounded-full">
                        {complex.badge}
                      </span>
                    </div>
                  </div>
                  <div className="p-4">
                    <h3 className="font-semibold text-foreground group-hover:text-brand transition-colors line-clamp-1">
                      {complex.name}
                    </h3>
                    <p className="text-sm text-muted-foreground mt-1">{complex.location}</p>
                    <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                        {complex.properties}
                      </span>
                      <span className="flex items-center gap-1">
                        <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        {complex.developer}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </section>

          {/* TRUST / BENEFITS ROW */}
          <section aria-labelledby="benefits-title" className="mb-12 border-t border-border/70 pt-10">
            <h2 id="benefits-title" className="text-xl font-semibold text-foreground mb-6 text-center">
              Niyə bizimlə?
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="rounded-xl bg-surface p-5 border border-border/50 text-center transition-all hover:border-brand/30 hover:shadow-sm">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-brand-soft text-brand mx-auto mb-3">
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="font-semibold text-foreground mb-1">Pulsuz elan yerləşdir</div>
                <div className="text-sm text-muted-foreground">Heç bir ödnişsiz, dərhal yerləşdirin</div>
              </div>
              <div className="rounded-xl bg-surface p-5 border border-border/50 text-center transition-all hover:border-brand/30 hover:shadow-sm">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-brand-soft text-brand mx-auto mb-3">
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <div className="font-semibold text-foreground mb-1">Təhlükəsiz ödəniş</div>
                <div className="text-sm text-muted-foreground">Qorunan əməliyyatlar, hər iki tərəf qorunur</div>
              </div>
              <div className="rounded-xl bg-surface p-5 border border-border/50 text-center transition-all hover:border-brand/30 hover:shadow-sm">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-brand-soft text-brand mx-auto mb-3">
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
                <div className="font-semibold text-foreground mb-1">24/7 Dəstək</div>
                <div className="text-sm text-muted-foreground">İstənilən vaxt, hər hansı bir sualınız varsa</div>
              </div>
              <div className="rounded-xl bg-surface p-5 border border-border/50 text-center transition-all hover:border-brand/30 hover:shadow-sm">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-brand-soft text-brand mx-auto mb-3">
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="font-semibold text-foreground mb-1">Mobil uyğun</div>
                <div className="text-sm text-muted-foreground">Telefonunuzdan rahat axtarış və idarəetmə</div>
              </div>
            </div>
          </section>

          {/* MAP BLOCK */}
          <section aria-labelledby="map-title" className="mb-12">
            <h2 id="map-title" className="text-xl font-semibold text-foreground mb-4">
              Xəritə üzərində elanlar
            </h2>
            <div className="h-80 w-full rounded-xl overflow-hidden border border-border/50">
              <MapView
                markers={mapMarkers}
                className="h-full w-full"
                showBoundsSearch={false}
                searchLabel=""
                initialBounds={{ north: 41.0, south: 39.0, east: 46.0, west: 44.0 }}
              />
            </div>
          </section>
        </main>
      </div>

      {/* RIGHT FULL RAIL - Flush against viewport edge */}
      <aside
        className="hidden xl:block fixed right-0 top-[228px] bottom-0 w-[120px] z-20 pointer-events-none"
      >
        <AdSlot
          placement="RIGHT_RAIL"
          className="w-full h-[600px] max-w-[120px]"
        />
      </aside>
    </div>
  );
}