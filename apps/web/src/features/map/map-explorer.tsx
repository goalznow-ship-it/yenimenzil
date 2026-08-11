"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { Property } from "@yenimenzil/types";
import type { MapMarkerData } from "@/lib/map/types";
import { MapView } from "@/features/map/map-view";
import { searchProperties } from "@/services/property-api";
import { useSearchFilters } from "@/features/search/use-search-filters";
import { FilterControls } from "@/features/search/filter-controls";
import { formatPriceShort, formatPriceWithPeriod } from "@/lib/format";
import { ImageWithFallback } from "@/components/common/image-with-fallback";
import { EmptyState } from "@yenimenzil/ui";
import { ArrowRight, SearchX, SlidersHorizontal, X } from "lucide-react";
import type { SortKey } from "@yenimenzil/types";

export function MapExplorer() {
  const { filters, setFilter, resetAll } = useSearchFilters();
  const searchParams = useSearchParams();
  const [filtersOpen, setFiltersOpen] = React.useState(false);
  const [activeId, setActiveId] = React.useState<string | null>(() =>
    searchParams.get("property")
  );
  const [listings, setListings] = React.useState<Property[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let cancelled = false;
    searchProperties({
      deal: filters.deal,
      district: filters.district,
      propertyType: filters.propertyType,
      rooms: filters.rooms,
      minPrice: filters.minPrice,
      maxPrice: filters.maxPrice,
      metro: filters.metro,
      sort: "newest" as SortKey
    })
      .then((res) => {
        if (cancelled) return;
        setListings(res.data);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setListings([]);
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [filters]);

  const markers = React.useMemo<MapMarkerData[]>(
    () =>
      listings.map((p) => ({
        id: p.id,
        point: p.location.point,
        price: p.price,
        formattedPrice: formatPriceShort(p.price),
        image: p.images[0]?.src,
        title: p.title,
        address: p.location.addressText
      })),
    [listings]
  );

  const activeListing =
    activeId != null ? listings.find((p) => p.id === activeId) : undefined;

  const filterProps = {
    filters,
    onDealChange: (deal: typeof filters.deal) => setFilter({ deal }),
    onDistrictChange: (district: string) => setFilter({ district }),
    onPropertyTypeChange: (propertyType: typeof filters.propertyType) =>
      setFilter({ propertyType }),
    onRoomsChange: (rooms: number[]) => setFilter({ rooms }),
    onPriceChange: (minPrice?: number, maxPrice?: number) =>
      setFilter({ minPrice, maxPrice }),
    onAreaChange: (minArea?: number, maxArea?: number) =>
      setFilter({ minArea, maxArea }),
    onMetroChange: (metro: string) => setFilter({ metro }),
    onBuildingTypeChange: (buildingType: "new" | "old" | undefined) =>
      setFilter({ buildingType }),
    onRepairChange: (repairStatus: string) =>
      setFilter({ repairStatus: repairStatus as typeof filters.repairStatus }),
    onOwnerOnlyChange: (ownerOnly: boolean) => setFilter({ ownerOnly }),
    onVerifiedChange: (verifiedOnly: boolean) => setFilter({ verifiedOnly }),
    onSortChange: (sort: SortKey) => setFilter({ sort }),
    onReset: resetAll
  };

  return (
    <div className="relative h-[calc(100dvh-4rem)] w-full overflow-hidden">
      <MapView
        markers={markers}
        className="absolute inset-0"
        showBoundsSearch={false}
        highlightedId={activeId}
        onMarkerClick={(marker) => setActiveId(marker.id)}
      />

      {/* Filter button (mobile) */}
      <button
        type="button"
        onClick={() => setFiltersOpen(true)}
        className="absolute left-3 top-3 z-10 flex items-center gap-2 rounded-full bg-surface px-4 py-2.5 text-sm font-medium shadow-card ring-1 ring-border/70 transition-colors hover:ring-brand/30"
      >
        <SlidersHorizontal className="h-4 w-4" />
        Filtrlər
      </button>

      {/* Result count chip */}
      <span className="absolute left-1/2 top-3 z-10 -translate-x-1/2 whitespace-nowrap rounded-full bg-surface px-4 py-2 text-sm font-semibold shadow-card ring-1 ring-border/70">
        {loading ? "Yüklənir…" : `${listings.length} elan`}
      </span>

      {/* Side panel with selected listing */}
      {activeListing ? (
        <div className="absolute inset-x-3 bottom-3 z-10 md:inset-x-auto md:left-3 md:right-auto md:top-14 md:w-[340px]">
          <div className="overflow-hidden rounded-2xl bg-surface shadow-lift ring-1 ring-brand/20">
            <div className="flex items-start justify-between border-b border-border/70 p-3">
              <p className="text-[13px] font-medium text-foreground/70">
                Xəritədə seçilən elan
              </p>
              <button
                type="button"
                onClick={() => setActiveId(null)}
                className="rounded-lg p-1 text-foreground/50 hover:bg-foreground/[0.05]"
                aria-label="Bağla"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="flex gap-3 p-3">
              <div className="relative h-28 w-32 shrink-0 overflow-hidden rounded-xl bg-foreground/[0.03]">
                {activeListing.images[0] ? (
                  <ImageWithFallback
                    src={activeListing.images[0].src}
                    alt={activeListing.images[0].alt}
                    fill
                    sizes="128px"
                    className="object-cover"
                  />
                ) : null}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[17px] font-semibold tracking-tight text-foreground">
                  {formatPriceWithPeriod(
                    activeListing.price,
                    activeListing.dealType
                  )}
                </p>
                <p className="mt-0.5 line-clamp-2 text-[13px] text-foreground/80">
                  {activeListing.title}
                </p>
                <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">
                  {activeListing.location.addressText}
                </p>
                <Link
                  href={`/property/${activeListing.id}`}
                  className="mt-2 inline-flex items-center gap-1 text-[13px] font-semibold text-brand hover:text-brand-hover"
                >
                  Elana bax
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {listings.length === 0 && !filtersOpen && !loading ? (
        <div className="absolute inset-x-3 top-20 z-10 md:left-1/2 md:right-auto md:-translate-x-1/2 md:top-16 md:w-[420px]">
          <EmptyState
            icon={<SearchX className="h-6 w-6" />}
            title="Bu ərazidə elan yoxdur"
            description="Xəritədə başqa əraziyə keçin və ya filtrləri dəyişin."
            action={
              <button
                type="button"
                onClick={resetAll}
                className="rounded-[10px] border border-border bg-surface px-4 py-2 text-sm font-medium"
              >
                Filtrləri təmizlə
              </button>
            }
          />
        </div>
      ) : null}

      {/* Filters bottom sheet */}
      {filtersOpen ? (
        <div className="absolute inset-0 z-20">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setFiltersOpen(false)}
          />
          <div className="absolute inset-x-0 bottom-0 max-h-[80dvh] overflow-y-auto rounded-t-[24px] bg-surface pb-8 shadow-2xl">
            <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-surface px-4 py-3.5">
              <h2 className="text-base font-semibold">Filtrlər</h2>
              <button
                type="button"
                onClick={() => setFiltersOpen(false)}
                className="rounded-lg p-1.5 text-foreground/50 hover:bg-foreground/[0.05]"
                aria-label="Bağla"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="mt-4">
              <FilterControls
                {...filterProps}
                onClose={() => setFiltersOpen(false)}
                variant="sheet"
              />
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
