"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import type { DealType } from "@yenimenzil/types";
import { PROPERTY_TYPE_LABELS, type PropertyType } from "@yenimenzil/types";
import { Button, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Tabs, TabsList, TabsTrigger } from "@yenimenzil/ui";
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
  const searchParams = useSearchParams();
  const [deal, setDeal] = React.useState<DealType>(searchParams.get("deal") as DealType || "sale");
  React.useEffect(() => {
    const dealParam = searchParams.get("deal");
    if (dealParam && (dealParam === "sale" || dealParam === "rent" || dealParam === "daily")) {
      window.setTimeout(() => {
        setDeal(dealParam as DealType);
      }, 0);
    }
  }, [searchParams]);
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

  return (
    <div>
      <Tabs value={deal} onValueChange={(v) => setDeal(v as DealType)} variant="underline" className="mb-4">
        <TabsList className="gap-6 bg-transparent p-0">
          <TabsTrigger value="sale" className="text-base font-medium px-1 py-2 text-foreground/60 hover:text-brand data-[state=active]:text-brand data-[state=active]:font-semibold">
            Al
          </TabsTrigger>
          <TabsTrigger value="rent" className="text-base font-medium px-1 py-2 text-foreground/60 hover:text-brand data-[state=active]:text-brand data-[state=active]:font-semibold">
            Kirayə
          </TabsTrigger>
          <TabsTrigger value="daily" className="text-base font-medium px-1 py-2 text-foreground/60 hover:text-brand data-[state=active]:text-brand data-[state=active]:font-semibold">
            Günlük
          </TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="rounded-2xl border border-border bg-surface p-4 shadow-lg md:p-5">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_0.9fr_1fr_auto]">
          <div className="relative">
            <MapPin className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-foreground/40" />
            <Select value={city} onValueChange={setCity}>
              <SelectTrigger className="pl-11 h-12">
                <SelectValue placeholder="Harada?" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Bütün bölgələr</SelectItem>
                {POPULAR_PLACES.map((place) => (
                  <SelectItem key={place.label} value={place.label}>
                    {place.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Select value={propertyType} onValueChange={setPropertyType}>
            <SelectTrigger className="h-12">
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
            <SelectTrigger className="h-12">
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
            <SelectTrigger className="h-12">
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

          <Button onClick={submit} size="lg" className="h-12 gap-2 lg:px-8 bg-brand hover:bg-brand/90 text-white font-semibold">
            <Search className="h-5 w-5" />
            Axtar
          </Button>
        </div>
      </div>
    </div>
  );
}