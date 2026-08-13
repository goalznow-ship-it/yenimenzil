"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import type { Property } from "@yenimenzil/types";
import type { MapBounds } from "@/lib/map/types";
import { isPointInBounds } from "@/lib/map/types";
import type { MapMarkerData } from "@/lib/map/types";
import { useSearchFilters, type ViewMode } from "./use-search-filters";
import { searchProperties } from "@/services/property-api";
import { MapView } from "@/features/map/map-view";
import { FilterControls } from "./filter-controls";
import { PropertyListRow } from "./property-list-row";
import { PropertyGrid } from "@/features/properties/property-grid";
import {
  EmptyState,
  cn,
  Skeleton,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@yenimenzil/ui";
import {
  LayoutGrid,
  List,
  Map as MapIcon,
  MapPin,
  SlidersHorizontal,
  X,
  SearchX
} from "lucide-react";
import { formatPriceShort } from "@/lib/format";
import type { SortKey } from "@yenimenzil/types";

function parseBoundsParam(searchParams: URLSearchParams): MapBounds | undefined {
  const north = Number(searchParams.get("north"));
  const south = Number(searchParams.get("south"));
  const east = Number(searchParams.get("east"));
  const west = Number(searchParams.get("west"));
  if (
    Number.isFinite(north) &&
    Number.isFinite(south) &&
    Number.isFinite(east) &&
    Number.isFinite(west) &&
    north > south &&
    east > west
  ) {
    return { north, south, east, west };
  }
  return undefined;
}

function activeFilterCount(filters: ReturnType<typeof useSearchFilters>["filters"]) {
  let count = 0;
  if (filters.district) count += 1;
  if (filters.propertyType !== "all") count += 1;
  if (filters.rooms.length > 0) count += 1;
  if (filters.minPrice != null || filters.maxPrice != null) count += 1;
  if (filters.minArea != null || filters.maxArea != null) count += 1;
  if (filters.metro) count += 1;
  if (filters.buildingType) count += 1;
  if (filters.repairStatus) count += 1;
  if (filters.ownerOnly) count += 1;
  if (filters.verifiedOnly) count += 1;
  if (filters.withPhoto) count += 1;
  if (filters.minYear != null || filters.maxYear != null) count += 1;
  if (filters.minFloor != null || filters.maxFloor != null) count += 1;
  return count;
}

export function SearchClient() {
  const { filters, setFilter, push, resetAll } = useSearchFilters();
  const searchParams = useSearchParams();

  const [view, setView] = React.useState<ViewMode>(() =>
    (searchParams.get("view") as ViewMode) ?? "list"
  );
  const [mapBounds, setMapBounds] = React.useState<MapBounds | undefined>(
    () => parseBoundsParam(searchParams)
  );
  const [boundsCommitted, setBoundsCommitted] = React.useState<boolean>(() =>
    parseBoundsParam(searchParams) !== undefined
  );
  const [mobileFiltersOpen, setMobileFiltersOpen] = React.useState(false);
  const [mapOpen, setMapOpen] = React.useState(false);
  const [activeMarkerId, setActiveMarkerId] = React.useState<string | null>(null);
  const [pendingBounds, setPendingBounds] = React.useState<MapBounds | null>(null);
  const [unfiltered, setUnfiltered] = React.useState<Property[]>([]);
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
      minArea: filters.minArea,
      maxArea: filters.maxArea,
      metro: filters.metro,
      buildingType: filters.buildingType,
      repairStatus: filters.repairStatus,
    ownerOnly: filters.ownerOnly,
    verifiedOnly: filters.verifiedOnly,
    withPhoto: filters.withPhoto,
    minYear: filters.minYear,
    maxYear: filters.maxYear,
    minFloor: filters.minFloor,
    maxFloor: filters.maxFloor,
    sort: filters.sort
    })
      .then((res) => {
        if (cancelled) return;
        setUnfiltered(res.data);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setUnfiltered([]);
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [filters]);

  const results = React.useMemo(() => {
    if (!mapBounds) return unfiltered;
    return unfiltered.filter((p) =>
      isPointInBounds(p.location.point, mapBounds)
    );
  }, [unfiltered, mapBounds]);

  const markers = React.useMemo<MapMarkerData[]>(
    () =>
      unfiltered.map((p) => ({
        id: p.id,
        point: p.location.point,
        price: p.price,
        formattedPrice: formatPriceShort(p.price),
        image: p.images[0]?.src,
        title: p.title,
        address: p.location.addressText
      })),
    [unfiltered]
  );

  const onSearchArea = () => {
    const bounds = pendingBounds ?? mapBounds;
    if (!bounds) return;
    setMapBounds(bounds);
    setBoundsCommitted(true);
    push({
      north: bounds.north,
      south: bounds.south,
      east: bounds.east,
      west: bounds.west
    });
    setPendingBounds(null);
  };

  const clearBounds = () => {
    setMapBounds(undefined);
    setBoundsCommitted(false);
    push({
      north: undefined,
      south: undefined,
      east: undefined,
      west: undefined
    });
  };

  const mapEl = (
    <MapView
      markers={markers}
      className="h-full w-full"
      showBoundsSearch
      searchLabel="Bu ərazidə axtar"
      initialBounds={boundsCommitted ? mapBounds : undefined}
      highlightedId={activeMarkerId}
      onBoundsChange={(bounds) => setPendingBounds(bounds)}
      onMarkerHover={(id) => setActiveMarkerId(id)}
      onSearchArea={onSearchArea}
    />
  );

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
    onWithPhotoChange: (withPhoto: boolean) => setFilter({ withPhoto }),
    onYearChange: (minYear?: number, maxYear?: number) =>
      setFilter({ minYear, maxYear }),
    onFloorChange: (minFloor?: number, maxFloor?: number) =>
      setFilter({ minFloor, maxFloor }),
    onSortChange: (sort: SortKey) => setFilter({ sort }),
    onReset: resetAll
  };

  const countLabel = loading
    ? "Yüklənir…"
    : mapBounds
      ? `${results.length} elan`
      : `${unfiltered.length} elan`;

  return (
    <div className="mx-auto max-w-[1440px] px-4 lg:px-6">
      {/* Desktop filter bar */}
      <div className="hidden rounded-2xl border border-border bg-surface p-3 lg:block">
        <FilterControls {...filterProps} />
      </div>

      {/* Mobile filter bar */}
      <div className="sticky top-16 z-30 -mx-4 border-b border-border/70 bg-background/95 px-4 py-2 backdrop-blur-md lg:hidden">
        <div className="flex items-center gap-2 overflow-x-auto pb-0.5">
          <div className="flex shrink-0 rounded-[10px] bg-foreground/[0.05] p-0.5">
            {(["sale", "rent", "daily"] as const).map((deal) => (
              <button
                key={deal}
                type="button"
                onClick={() => setFilter({ deal })}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors",
                  filters.deal === deal
                    ? "bg-surface text-foreground shadow-sm"
                    : "text-foreground/60"
                )}
              >
                {deal === "sale" ? "Al" : deal === "rent" ? "Kirayə" : "Günlük"}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setMobileFiltersOpen(true)}
            className="flex shrink-0 items-center gap-1.5 rounded-[10px] border border-border bg-surface px-3 py-2 text-[13px] font-medium text-foreground/75"
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            Filtrlər
            {activeFilterCount(filters) > 0 ? (
              <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-brand px-1 text-[10px] font-semibold text-white">
                {activeFilterCount(filters)}
              </span>
            ) : null}
          </button>
          {boundsCommitted ? (
            <button
              type="button"
              onClick={clearBounds}
              className="flex shrink-0 items-center gap-1 rounded-[10px] border border-brand/30 bg-brand-soft px-3 py-2 text-[13px] font-medium text-brand"
            >
              Xəritə ərazisi
              <X className="h-3.5 w-3.5" />
            </button>
          ) : null}
        </div>
      </div>

      {/* Results header */}
      <div className="mt-4 flex items-center justify-between gap-3 lg:mt-5">
        <div className="flex items-center gap-2">
          <span className="text-[15px] font-semibold text-foreground">
            {countLabel}
          </span>
          {boundsCommitted ? (
            <button
              type="button"
              onClick={clearBounds}
              className="hidden items-center gap-1 rounded-full border border-brand/30 bg-brand-soft px-2.5 py-0.5 text-xs font-medium text-brand lg:flex"
            >
              <MapPin className="h-3 w-3" />
              Xəritə ərazisi
              <X className="h-3 w-3" />
            </button>
          ) : null}
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden sm:block">
            <Select
              value={filters.sort}
              onValueChange={(v) => setFilter({ sort: v as SortKey })}
            >
              <SelectTrigger className="h-9 w-44 text-[13px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="newest">Ən yeni</SelectItem>
                <SelectItem value="price_asc">Qiymət (artan)</SelectItem>
                <SelectItem value="price_desc">Qiymət (azalan)</SelectItem>
                <SelectItem value="area_desc">Sahə (azalan)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="hidden items-center rounded-[10px] border border-border bg-surface p-0.5 lg:flex">
            {(
              [
                { value: "list", icon: List, label: "Siyahı" },
                { value: "grid", icon: LayoutGrid, label: "Şəbəkə" },
                { value: "map", icon: MapIcon, label: "Xəritə" }
              ] as const
            ).map((mode) => (
              <button
                key={mode.value}
                type="button"
                aria-label={mode.label}
                aria-pressed={view === mode.value}
                onClick={() => setView(mode.value)}
                className={cn(
                  "flex h-8 w-9 items-center justify-center rounded-lg transition-colors",
                  view === mode.value
                    ? "bg-brand text-white"
                    : "text-foreground/60 hover:text-foreground"
                )}
              >
                <mode.icon className="h-4 w-4" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Desktop: split results + map */}
      <div className="mt-4 hidden gap-5 lg:grid lg:grid-cols-[1.25fr_1fr]">
        <div className={cn(view === "map" && "hidden")}>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="flex gap-4 rounded-2xl bg-surface p-3 ring-1 ring-border/70"
                >
                  <Skeleton className="h-40 w-44 rounded-xl sm:w-56" />
                  <div className="flex-1 space-y-2.5 py-1">
                    <Skeleton className="h-5 w-1/3" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3.5 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : results.length === 0 ? (
            <EmptyState
              icon={<SearchX className="h-7 w-7" />}
              title="Heç bir elan tapılmadı"
              description="Axtarış şərtlərinə uyğun elan yoxdur. Filtrləri yumşaldın və ya xəritə ərazisini genişləndirin."
              action={
                <button
                  type="button"
                  onClick={() => {
                    if (boundsCommitted) clearBounds();
                    resetAll();
                  }}
                  className="rounded-[10px] border border-border bg-surface px-4 py-2 text-sm font-medium text-foreground/80 hover:border-foreground/25"
                >
                  Filtrləri təmizlə
                </button>
              }
            />
          ) : view === "list" ? (
            <div className="space-y-3">
              {results.map((p) => (
                <div
                  key={p.id}
                  onMouseEnter={() => setActiveMarkerId(p.id)}
                  onMouseLeave={() => setActiveMarkerId(null)}
                >
                  <PropertyListRow property={p} />
                </div>
              ))}
            </div>
          ) : (
            <PropertyGrid listings={results} columns={3} />
          )}
        </div>

        <div
          className={cn(
            "sticky top-20 h-[calc(100dvh-6rem)] overflow-hidden rounded-2xl shadow-card ring-1 ring-border/70",
            view === "map" && "col-span-2 h-[calc(100dvh-10rem)]"
          )}
        >
          {mapEl}
        </div>
      </div>

      {/* Mobile: list */}
      <div className="mt-3 lg:hidden">
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="flex gap-4 rounded-2xl bg-surface p-3 ring-1 ring-border/70"
              >
                <Skeleton className="h-32 w-36 rounded-xl sm:w-48" />
                <div className="flex-1 space-y-2.5 py-1">
                  <Skeleton className="h-5 w-1/3" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3.5 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : results.length === 0 ? (
          <EmptyState
            icon={<SearchX className="h-7 w-7" />}
            title="Heç bir elan tapılmadı"
            description="Axtarış şərtlərinə uyğun elan yoxdur. Filtrləri yumşaldın."
            action={
              <button
                type="button"
                onClick={resetAll}
                className="rounded-[10px] border border-border bg-surface px-4 py-2 text-sm font-medium text-foreground/80"
              >
                Filtrləri təmizlə
              </button>
            }
          />
        ) : (
          <div className="space-y-3">
            {results.map((p) => (
              <PropertyListRow key={p.id} property={p} />
            ))}
          </div>
        )}
      </div>

      {/* Mobile map overlay */}
      {mapOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0">
            {mapEl}
            <button
              type="button"
              onClick={() => setMapOpen(false)}
              className="absolute left-3 top-3 flex h-10 w-10 items-center justify-center rounded-full bg-surface shadow-card ring-1 ring-black/5 transition-transform active:scale-95"
              aria-label="Xəritəni bağla"
            >
              <X className="h-5 w-5" />
            </button>
            <button
              type="button"
              onClick={onSearchArea}
              className="absolute bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-brand px-5 py-2.5 text-sm font-semibold text-white shadow-lg"
            >
              Bu ərazidə axtar
            </button>
          </div>
        </div>
      ) : null}

      {/* Mobile map toggle */}
      <button
        type="button"
        onClick={() => setMapOpen(true)}
        className="fixed bottom-20 right-4 z-30 flex items-center gap-2 rounded-full bg-brand px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand/30 lg:hidden"
      >
        <MapIcon className="h-4 w-4" />
        Xəritə
      </button>

      {/* Mobile filters bottom sheet */}
      {mobileFiltersOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
            onClick={() => setMobileFiltersOpen(false)}
          />
          <div className="absolute inset-x-0 bottom-0 max-h-[85dvh] overflow-y-auto rounded-t-[24px] bg-surface pb-8 shadow-2xl">
            <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-surface px-4 py-3.5">
              <h2 className="text-base font-semibold">Filtrlər</h2>
              <button
                type="button"
                onClick={() => setMobileFiltersOpen(false)}
                className="rounded-lg p-1.5 text-foreground/50 hover:bg-foreground/[0.05]"
                aria-label="Bağla"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="mt-4">
              <FilterControls {...filterProps} onClose={() => setMobileFiltersOpen(false)} variant="sheet" />
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function SearchResultsSkeleton() {
  return (
    <div className="mx-auto max-w-[1440px] px-4 lg:px-6">
      <div className="mt-4 hidden rounded-2xl border border-border bg-surface p-3 lg:block">
        <Skeleton className="h-10 w-full" />
      </div>
      <div className="mt-5 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex gap-4 rounded-2xl bg-surface p-3 ring-1 ring-border/70">
            <Skeleton className="h-40 w-44 rounded-xl sm:w-56" />
            <div className="flex-1 space-y-2.5 py-1">
              <Skeleton className="h-5 w-1/3" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3.5 w-1/2" />
              <Skeleton className="h-3.5 w-2/3" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
