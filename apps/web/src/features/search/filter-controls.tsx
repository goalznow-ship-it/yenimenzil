"use client";

import * as React from "react";
import type { DealType, SortKey } from "@yenimenzil/types";
import { PROPERTY_TYPE_LABELS, type PropertyType } from "@yenimenzil/types";
import {
  Button,
  cn,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Tabs,
  TabsList,
  TabsTrigger
} from "@yenimenzil/ui";
import { SlidersHorizontal } from "lucide-react";
import { DISTRICTS, METRO_STATIONS, POPULAR_PLACES } from "@/data/locations";
import type { UrlFilters } from "./use-search-filters";
import { normalizeAz } from "@/services/listings-service";

const ROOMS = [
  { value: 1, label: "1" },
  { value: 2, label: "2" },
  { value: 3, label: "3" },
  { value: 4, label: "4+" }
];

interface FilterControlsProps {
  filters: UrlFilters;
  onDealChange: (deal: DealType) => void;
  onDistrictChange: (value: string) => void;
  onPropertyTypeChange: (value: PropertyType | "all") => void;
  onRoomsChange: (rooms: number[]) => void;
  onPriceChange: (min?: number, max?: number) => void;
  onAreaChange: (min?: number, max?: number) => void;
  onMetroChange: (value: string) => void;
  onBuildingTypeChange: (value: "new" | "old" | undefined) => void;
  onRepairChange: (value: string) => void;
  onOwnerOnlyChange: (value: boolean) => void;
  onVerifiedChange: (value: boolean) => void;
  onSortChange: (value: SortKey) => void;
  onReset: () => void;
  onClose?: () => void;
  variant?: "bar" | "sheet";
}

const REPAIR_OPTIONS = [
  { value: "renovated", label: "Təmirli" },
  { value: "cosmetic", label: "Kosmetik təmir" },
  { value: "needs_repair", label: "Təmir tələb olunur" },
  { value: "none", label: "Təmirsiz" }
];

function NumberInput({
  value,
  onValueChange,
  placeholder,
  ariaLabel
}: {
  value: number | undefined;
  onValueChange: (value: number | undefined) => void;
  placeholder: string;
  ariaLabel: string;
}) {
  return (
    <Input
      type="number"
      inputMode="numeric"
      min={0}
      placeholder={placeholder}
      aria-label={ariaLabel}
      value={value ?? ""}
      onChange={(e) => {
        const v = e.target.value;
        onValueChange(v === "" ? undefined : Math.max(0, Number(v)));
      }}
    />
  );
}

export function FilterControls({
  filters,
  onDealChange,
  onDistrictChange,
  onPropertyTypeChange,
  onRoomsChange,
  onPriceChange,
  onAreaChange,
  onMetroChange,
  onBuildingTypeChange,
  onRepairChange,
  onOwnerOnlyChange,
  onVerifiedChange,
  onSortChange,
  onReset,
  onClose,
  variant = "bar"
}: FilterControlsProps) {
  const [advancedOpen, setAdvancedOpen] = React.useState(variant === "sheet");
  const isSheet = variant === "sheet";

  const districtOptions = React.useMemo(() => {
    const seen = new Set<string>();
    const options: { value: string; label: string }[] = [];
    for (const place of POPULAR_PLACES) {
      const key = normalizeAz(place.label);
      if (seen.has(key)) continue;
      seen.add(key);
      options.push({ value: place.label, label: place.label });
    }
    for (const d of DISTRICTS) {
      const label = d.neighborhood ?? d.settlement ?? d.district;
      const key = normalizeAz(label);
      if (seen.has(key)) continue;
      seen.add(key);
      options.push({ value: label, label });
    }
    return options;
  }, []);

  const toggleRoom = (room: number) => {
    const next = filters.rooms.includes(room)
      ? filters.rooms.filter((r) => r !== room)
      : [...filters.rooms, room];
    onRoomsChange(next.length === 0 ? [] : next);
  };

  return (
    <div className={cn("w-full", isSheet && "px-4 pb-6")}>
      <div className={cn(isSheet ? "space-y-5" : "space-y-3")}>
        <Tabs
          value={filters.deal}
          onValueChange={(v) => onDealChange(v as DealType)}
          variant="underline"
        >
          <TabsList className="gap-4">
            <TabsTrigger value="sale">Al</TabsTrigger>
            <TabsTrigger value="rent">Kirayə</TabsTrigger>
            <TabsTrigger value="daily">Günlük</TabsTrigger>
          </TabsList>
        </Tabs>

        <div className={cn("grid gap-2", isSheet ? "grid-cols-2" : "grid-cols-2 xl:grid-cols-4")}>
          <Select value={filters.district} onValueChange={onDistrictChange}>
            <SelectTrigger className="h-10">
              <SelectValue placeholder="Ərazi" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Bütün ərazilər</SelectItem>
              {districtOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={filters.propertyType}
            onValueChange={(v) => onPropertyTypeChange(v as PropertyType | "all")}
          >
            <SelectTrigger className="h-10">
              <SelectValue placeholder="Əmlak növü" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Bütün növlər</SelectItem>
              {(
                Object.entries(PROPERTY_TYPE_LABELS) as [
                  PropertyType,
                  string
                ][]
              ).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filters.metro} onValueChange={onMetroChange}>
            <SelectTrigger className="h-10">
              <SelectValue placeholder="Metro" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">İstənilən metro</SelectItem>
              {METRO_STATIONS.map((metro) => (
                <SelectItem key={metro} value={metro}>
                  {metro}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={filters.sort}
            onValueChange={(v) => onSortChange(v as SortKey)}
          >
            <SelectTrigger className="h-10">
              <SelectValue placeholder="Sıralama" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Ən yeni</SelectItem>
              <SelectItem value="price_asc">Qiymət (artan)</SelectItem>
              <SelectItem value="price_desc">Qiymət (azalan)</SelectItem>
              <SelectItem value="area_desc">Sahə (azalan)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <span className="mb-1.5 block text-[13px] font-medium text-foreground/70">
            Otaqlar
          </span>
          <div className="flex flex-wrap gap-1.5">
            {ROOMS.map((room) => (
              <button
                key={room.value}
                type="button"
                aria-pressed={filters.rooms.includes(room.value)}
                onClick={() => toggleRoom(room.value)}
                className={cn(
                  "h-9 min-w-11 rounded-[10px] border px-3 text-sm font-medium transition-colors",
                  filters.rooms.includes(room.value)
                    ? "border-brand bg-brand text-white"
                    : "border-border bg-surface text-foreground/75 hover:border-foreground/25"
                )}
              >
                {room.label}
              </button>
            ))}
            {filters.rooms.length > 0 ? (
              <button
                type="button"
                onClick={() => onRoomsChange([])}
                className="h-9 rounded-[10px] px-3 text-sm font-medium text-muted-foreground underline-offset-4 hover:underline"
              >
                Təmizlə
              </button>
            ) : null}
          </div>
        </div>

        <div className={cn("grid gap-2", isSheet ? "grid-cols-2" : "grid-cols-2 xl:grid-cols-4")}>
          <NumberInput
            value={filters.minPrice}
            onValueChange={(v) => onPriceChange(v, filters.maxPrice)}
            placeholder="Min qiymət (₼)"
            ariaLabel="Minimum qiymət"
          />
          <NumberInput
            value={filters.maxPrice}
            onValueChange={(v) => onPriceChange(filters.minPrice, v)}
            placeholder="Maks qiymət (₼)"
            ariaLabel="Maksimum qiymət"
          />
          <NumberInput
            value={filters.minArea}
            onValueChange={(v) => onAreaChange(v, filters.maxArea)}
            placeholder="Min sahə (m²)"
            ariaLabel="Minimum sahə"
          />
          <NumberInput
            value={filters.maxArea}
            onValueChange={(v) => onAreaChange(filters.minArea, v)}
            placeholder="Maks sahə (m²)"
            ariaLabel="Maksimum sahə"
          />
        </div>

        {isSheet ? (
          <>
            <div className="h-px bg-border" />

            <div className="space-y-4">
              <div>
                <span className="mb-1.5 block text-[13px] font-medium text-foreground/70">
                  Tikili növü
                </span>
                <div className="flex gap-2">
                  {[
                    { value: undefined, label: "Hamısı" },
                    { value: "new", label: "Yeni tikili" },
                    { value: "old", label: "Köhnə tikili" }
                  ].map((option) => (
                    <button
                      key={option.label}
                      type="button"
                      onClick={() =>
                        onBuildingTypeChange(
                          option.value as "new" | "old" | undefined
                        )
                      }
                      className={cn(
                        "h-9 rounded-[10px] border px-3.5 text-[13px] font-medium transition-colors",
                        filters.buildingType === option.value
                          ? "border-brand bg-brand text-white"
                          : "border-border bg-surface text-foreground/75"
                      )}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <span className="mb-1.5 block text-[13px] font-medium text-foreground/70">
                  Təmir vəziyyəti
                </span>
                <Select value={filters.repairStatus ?? ""} onValueChange={onRepairChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="İstənilən" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">İstənilən</SelectItem>
                    {REPAIR_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                {[
                  {
                    label: "Yalnız mülkiyyətçilər",
                    value: filters.ownerOnly,
                    onChange: onOwnerOnlyChange
                  },
                  {
                    label: "Yalnız təsdiqlənmiş elanlar",
                    value: filters.verifiedOnly,
                    onChange: onVerifiedChange
                  }
                ].map((option) => (
                  <label
                    key={option.label}
                    className="flex cursor-pointer items-center justify-between rounded-xl border border-border bg-surface px-4 py-3"
                  >
                    <span className="text-sm font-medium text-foreground/80">
                      {option.label}
                    </span>
                    <button
                      type="button"
                      role="switch"
                      aria-checked={option.value}
                      onClick={() => option.onChange(!option.value)}
                      className={cn(
                        "relative h-6 w-11 rounded-full transition-colors",
                        option.value ? "bg-brand" : "bg-foreground/15"
                      )}
                    >
                      <span
                        className={cn(
                          "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform",
                          option.value ? "translate-x-[22px]" : "translate-x-0.5"
                        )}
                      />
                    </button>
                  </label>
                ))}
              </div>
            </div>
          </>
        ) : (
          <button
            type="button"
            onClick={() => setAdvancedOpen((v) => !v)}
            className="flex items-center gap-1.5 text-[13px] font-medium text-foreground/70 transition-colors hover:text-foreground"
          >
            <SlidersHorizontal className="h-4 w-4" />
            Daha çox filtr
            <span className="text-foreground/40">{advancedOpen ? "▲" : "▼"}</span>
          </button>
        )}

        {!isSheet && advancedOpen ? (
          <div className="grid grid-cols-2 gap-2 border-t border-border pt-3 xl:grid-cols-4">
            <div className="flex items-center gap-1.5">
              {[
                { value: "new", label: "Yeni" },
                { value: "old", label: "Köhnə" }
              ].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() =>
                    onBuildingTypeChange(
                      filters.buildingType === option.value
                        ? undefined
                        : (option.value as "new" | "old")
                    )
                  }
                  className={cn(
                    "h-9 rounded-[10px] border px-3 text-[13px] font-medium transition-colors",
                    filters.buildingType === option.value
                      ? "border-brand bg-brand text-white"
                      : "border-border bg-surface text-foreground/75"
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <Select
              value={filters.repairStatus ?? ""}
              onValueChange={onRepairChange}
            >
              <SelectTrigger>
                <SelectValue placeholder="Təmir vəziyyəti" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">İstənilən</SelectItem>
                {REPAIR_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex items-center gap-2">
              {[
                { label: "Mülkiyyətçi", checked: filters.ownerOnly, onChange: onOwnerOnlyChange },
                { label: "Təsdiqlənmiş", checked: filters.verifiedOnly, onChange: onVerifiedChange }
              ].map((option) => (
                <label
                  key={option.label}
                  className="flex cursor-pointer items-center gap-1.5 text-[13px] text-foreground/75"
                >
                  <input
                    type="checkbox"
                    checked={option.checked}
                    onChange={(e) => option.onChange(e.target.checked)}
                    className="h-4 w-4 rounded accent-brand"
                  />
                  {option.label}
                </label>
              ))}
            </div>
            <Button variant="ghost" size="sm" onClick={onReset} className="justify-self-start text-muted-foreground">
              Filtrləri təmizlə
            </Button>
          </div>
        ) : null}

        {isSheet ? (
          <div className="flex gap-2 pt-2">
            <Button variant="secondary" className="flex-1" onClick={onReset}>
              Təmizlə
            </Button>
            <Button className="flex-1" onClick={onClose}>
              Nəticələri göstər
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
