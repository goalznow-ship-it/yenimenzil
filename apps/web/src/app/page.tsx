import Link from "next/link";
import { SectionHeading } from "@yenimenzil/ui";
import { HomeTopBanner } from "@/components/ads/home-top-banner";
import { Header } from "@/components/layout/header";
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
  return (
    <div data-homepage-version="idealev-v5" className="relative overflow-x-hidden min-h-screen">
      <HomeTopBanner />
      <Header />
      <main className="relative grid grid-cols-[minmax(0,1fr)_minmax(0,1240px)_minmax(0,1fr)] gap-0">
        <aside className="col-span-1 bg-blue-50 border-r border-gray-200">
          <AdSlot placement="LEFT_RAIL" className="w-full h-full object-cover" />
        </aside>
        <div className="col-span-1 min-h-[calc(100dvh-11rem)] p-4">
          <Suspense fallback={<div className="h-64 flex items-center justify-center">Loading...</div>}>
            <HeroSection />
          </Suspense>
          <section aria-labelledby="categories-title" className="mb-4">
            <h2 id="categories-title" className="text-xl font-semibold text-foreground">Elan növü</h2>
            <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
              <a href="/search?deal=sale&property_type=new_building" className="rounded-xl bg-surface px-3 py-4">Yeni tikili</a>
              <a href="/search?deal=sale&property_type=old_building" className="rounded-xl bg-surface px-3 py-4">Köhnə tikili</a>
              <a href="/search?deal=sale&property_type=house" className="rounded-xl bg-surface px-3 py-4">Həyət evi / Bağ evi</a>
              <a href="/search?deal=sale&property_type=office" className="rounded-xl bg-surface px-3 py-4">Ofis</a>
              <a href="/search?deal=sale&property_type=garage" className="rounded-xl bg-surface px-3 py-4">Qaraj</a>
              <a href="/search?deal=sale&property_type=land" className="rounded-xl bg-surface px-3 py-4">Torpaq</a>
              <a href="/search?deal=sale&property_type=commercial" className="rounded-xl bg-surface px-3 py-4">Obyekt</a>
            </div>
          </section>
          <section aria-labelledby="popular-locations-title" className="mb-4">
            <h2 id="popular-locations-title" className="text-xl font-semibold text-foreground mb-3">
              Populyar_ENVIRONLER
            </h2>
            <div className="flex flex-wrap gap-2">
              <a href="/search?deal=sale&district=Bakı" className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3.5 py-1.5 text-[13px] font-medium text-foreground/70 shadow-sm">Bakı</a>
            </div>
          </section>
        </div>
        <aside className="col-span-1 bg-red-50 border-l border-gray-200">
          <AdSlot placement="RIGHT_RAIL" className="w-full h-full object-cover" />
        </aside>
      </main>
    </div>
  );
}
