"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import type { DealType } from "@yenimenzil/types";
import { PROPERTY_TYPE_LABELS, type PropertyType } from "@yenimenzil/types";
import { Button, cn, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Tabs, TabsList, TabsTrigger } from "@yenimenzil/ui";
import { MapPin, Search } from "lucide-react";
import { POPULAR_PLACES } from "@/data/locations";

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

export function SearchBar() {
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
      <Tabs value={deal} onValueChange={(v) => setDeal(v as DealType)} variant="underline" className="mb-3.5 max-w-md">
        <TabsList className="gap-5">
          <TabsTrigger value="sale" className="text-[16px]">
            Al
          </TabsTrigger>
          <TabsTrigger value="rent" className="text-[16px]">
            Kirayə
          </TabsTrigger>
          <TabsTrigger value="daily" className="text-[16px]">
            Günlük
          </TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="rounded-2xl border border-border bg-surface p-3 shadow-panel md:p-3.5">
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_0.8fr_1fr_auto]">
          <div className="relative">
            <MapPin className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
            <Select value={city} onValueChange={setCity}>
              <SelectTrigger className="pl-9">
                <SelectValue placeholder="Harada?" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Bütün ərazilər</SelectItem>
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

          <Select value={rooms} onValueChange={setRooms}>
            <SelectTrigger>
              <SelectValue placeholder="Otaq" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">İstənilən</SelectItem>
              {ROOM_OPTIONS.map((room) => (
                <SelectItem key={room.value} value={room.value}>
                  {room.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={price} onValueChange={setPrice}>
            <SelectTrigger>
              <SelectValue placeholder="Qiymət" />
            </SelectTrigger>
            <SelectContent>
              {PRICE_OPTIONS.map((option) => (
                <SelectItem key={option.label} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button onClick={submit} size="lg" className="gap-2 lg:px-8">
            <Search className="h-4 w-4" />
            Axtar
          </Button>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-[13px] text-muted-foreground">
          Populyar ərazilər:
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
