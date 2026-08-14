"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import type { DealType } from "@yenimenzil/types";
import { PROPERTY_TYPE_LABELS, type PropertyType } from "@yenimenzil/types";
import { Button, cn, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Tabs, TabsList, TabsTrigger } from "@yenimenzil/ui";
import { BriefcaseBusiness, Building2, House, Map, MapPin, Search, SlidersHorizontal, Warehouse } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { POPULAR_PLACES } from "@/data/locations";
import { useI18n } from "@/components/i18n-provider";
import { roomLabel, type MessageKey } from "@/lib/i18n";

const ROOM_OPTIONS = [
  { value: "1", label: "1 otaq" },
  { value: "2", label: "2 otaq" },
  { value: "3", label: "3 otaq" },
  { value: "4+", label: "4+ otaq" }
];

const PRICE_OPTIONS = [
  { value: "", label: "Qiymət" },
  { value: "0-100000", label: "100 000 ₼-ə qədər" },
  { value: "100000-200000", label: "100 000 — 200 000 ₼" },
  { value: "200000-400000", label: "200 000 — 400 000 ₼" },
  { value: "400000-", label: "400 000 ₼-dən" }
];

const CATEGORY_OPTIONS: Array<{ value: string; label: string; icon: LucideIcon }> = [
  { value: "new_building", label: "Yeni tikili", icon: Building2 },
  { value: "old_building", label: "Köhnə tikili", icon: Building2 },
  { value: "house", label: "Həyət evi/Bağ evi", icon: House },
  { value: "office", label: "Ofis", icon: BriefcaseBusiness },
  { value: "garage", label: "Qaraj", icon: Warehouse },
  { value: "land", label: "Torpaq", icon: Map },
  { value: "commercial", label: "Obyekt", icon: Building2 }
];

export function SearchBar() {
  const { locale, t } = useI18n();
  const router = useRouter();
  const [deal, setDeal] = React.useState<DealType>("sale");
  const [city, setCity] = React.useState("");
  const [propertyType, setPropertyType] = React.useState<string>("all");
  const [rooms, setRooms] = React.useState<string>("");
  const [price, setPrice] = React.useState<string>("");

  const buildQuery = (overrides?: Record<string, string>) => {
    const params = new URLSearchParams({ deal });
    if (overrides?.deal) params.set("deal", overrides.deal);
    if (city) params.set("district", city);
    if (propertyType !== "all") params.set("property_type", propertyType);
    if (rooms) {
      params.set("rooms", rooms === "4+" ? "4plus" : rooms);
    }
    if (price) {
      const [min, max] = price.split("-");
      if (min) params.set("min_price", min);
      if (max) params.set("max_price", max);
    }
    return params;
  };

  const submit = () => {
    router.push(`/search?${buildQuery().toString()}`);
  };

  const goToPopular = (label: string) => {
    router.push(`/search?${buildQuery({ district: label }).toString()}`);
  };

  return (
    <div>
      <Tabs value={deal} onValueChange={(v) => setDeal(v as DealType)} variant="underline" className="mb-3 max-w-md">
        <TabsList className="gap-5">
          <TabsTrigger value="sale" className="text-[16px]">
            {t("nav.sale")}
          </TabsTrigger>
          <TabsTrigger value="rent" className="text-[16px]">
            {t("nav.rent")}
          </TabsTrigger>
          <TabsTrigger value="daily" className="text-[16px]">
            {t("nav.daily")}
          </TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="rounded-2xl border border-border bg-surface p-3 shadow-panel md:p-3.5">
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-[1.35fr_1fr_0.8fr_1fr_auto_auto]">
          <div className="relative">
            <MapPin className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
            <Select value={city} onValueChange={setCity}>
              <SelectTrigger className="pl-9">
                <SelectValue placeholder={t("search.where")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">{t("search.allAreas")}</SelectItem>
                {POPULAR_PLACES.map((place) => (
                  <SelectItem key={place.label} value={place.label}>
                    {place.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Select value={propertyType} onValueChange={setPropertyType}>
            <SelectTrigger>
              <SelectValue placeholder={t("search.propertyType")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("search.allTypes")}</SelectItem>
              {(
                Object.entries(PROPERTY_TYPE_LABELS) as [
                  PropertyType,
                  string
                ][]
              ).map(([value]) => (
                <SelectItem key={value} value={value}>
                  {t(`type.${value}` as MessageKey)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={rooms} onValueChange={setRooms}>
            <SelectTrigger>
              <SelectValue placeholder={t("search.rooms")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">{t("search.any")}</SelectItem>
              {ROOM_OPTIONS.map((room) => (
                <SelectItem key={room.value} value={room.value}>
                  {room.value} {roomLabel(locale, Number.parseInt(room.value, 10))}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={price} onValueChange={setPrice}>
            <SelectTrigger>
              <SelectValue placeholder={t("search.price")} />
            </SelectTrigger>
            <SelectContent>
              {PRICE_OPTIONS.map((option) => (
                <SelectItem key={option.label} value={option.value}>
                  {option.value === "" ? t("search.price") : option.value === "0-100000" ? `100 000 ₼ ${t("search.upTo")}` : option.value === "400000-" ? `${t("search.from")} 400 000 ₼` : option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button onClick={() => router.push(`/search?${buildQuery().toString()}`)} size="lg" variant="secondary" className="gap-2">
            <SlidersHorizontal className="h-4 w-4" /> Filtrlər
          </Button>

          <Button onClick={submit} size="lg" className="gap-2 lg:px-8">
            <Search className="h-4 w-4" />
            {t("action.search")}
          </Button>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {CATEGORY_OPTIONS.map(({ value, label, icon: Icon }) => <button key={value} type="button" onClick={() => router.push(`/search?deal=${deal}&property_type=${value}`)} className="flex items-center gap-2 rounded-full bg-foreground/[0.045] px-4 py-2 text-[13px] font-medium hover:bg-brand-soft hover:text-brand"><Icon className="h-4 w-4"/>{label}</button>)}
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-[13px] text-muted-foreground">
          {t("search.popular")}
        </span>
        {POPULAR_PLACES.slice(0, 8).map((place) => (
          <button
            key={place.label}
            type="button"
            onClick={() => goToPopular(place.label)}
            className={cn(
              "rounded-full border border-border bg-surface px-3.5 py-1.5 text-[13px] font-medium text-foreground/65 shadow-sm transition-all hover:-translate-y-px hover:border-brand/40 hover:text-brand"
            )}
          >
            {place.label}
          </button>
        ))}
      </div>
    </div>
  );
}
