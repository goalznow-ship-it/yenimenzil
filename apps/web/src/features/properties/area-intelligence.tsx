"use client";

import * as React from "react";
import type { Property } from "@yenimenzil/types";
import { formatDistance } from "@/lib/geo";
import { nearestPlaces } from "@/data/pois";
import { MapPin, TrainFront, School, ShoppingBasket, TreePine, Hospital } from "lucide-react";
import { MapView } from "@/features/map/map-view";
import type { MapMarkerData } from "@/lib/map/types";

const KIND_ICONS = {
  metro: TrainFront,
  school: School,
  market: ShoppingBasket,
  park: TreePine,
  hospital: Hospital
} as const;

const KIND_LABELS = {
  metro: "Metro",
  school: "Məktəb",
  market: "Market",
  park: "Park",
  hospital: "Xəstəxana"
} as const;

export function AreaIntelligence({ property }: { property: Property }) {
  const point = property.location.point;

  const nearby = React.useMemo(() => {
    const nearestMetro = nearestPlaces(point, 1, ["metro"])[0];
    const others = nearestPlaces(point, 6, [
      "school",
      "market",
      "park",
      "hospital"
    ]);
    return { nearestMetro, others };
  }, [point]);

  const marker: MapMarkerData[] = [
    {
      id: property.id,
      point,
      price: property.price,
      formattedPrice: ""
    }
  ];

  const showMap = React.useMemo(() => {
    return {
      lat: point.lat,
      lng: point.lng
    };
  }, [point]);

  return (
    <section
      aria-labelledby="area-title"
      className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70"
    >
      <h2
        id="area-title"
        className="flex items-center gap-2 text-base font-semibold text-foreground"
      >
        <MapPin className="h-4.5 w-4.5 text-brand" />
        Ərazi haqqında
      </h2>

      <ul className="mt-4 space-y-2.5">
        {nearby.nearestMetro ? (
          <li className="flex items-center justify-between rounded-xl bg-brand-soft/60 px-4 py-3 text-sm">
            <span className="flex items-center gap-2 font-medium text-foreground/85">
              <TrainFront className="h-4 w-4 text-brand" />
              {nearby.nearestMetro.name}
            </span>
            <span className="font-semibold text-brand">
              {formatDistance(nearby.nearestMetro.distanceMeters)}
            </span>
          </li>
        ) : null}
        {nearby.others.map((place) => {
          const Icon = KIND_ICONS[place.kind];
          return (
            <li
              key={place.name}
              className="flex items-center justify-between px-1 py-1 text-sm"
            >
              <span className="flex items-center gap-2 text-foreground/80">
                <Icon className="h-4 w-4 text-foreground/40" />
                <span className="flex items-center gap-1.5">
                  {place.name}
                  <span className="rounded bg-foreground/[0.05] px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-foreground/50">
                    {KIND_LABELS[place.kind]}
                  </span>
                </span>
              </span>
              <span className="text-muted-foreground">
                {formatDistance(place.distanceMeters)}
              </span>
            </li>
          );
        })}
      </ul>

      <div className="mt-4 h-56 overflow-hidden rounded-2xl shadow-card ring-1 ring-border/70">
        <MapView
          markers={marker}
          center={showMap}
          zoom={14.5}
          className="h-full w-full"
        />
      </div>
      <p className="mt-3 text-[11px] text-foreground/40">
        Məsafələr koordinatlar əsasında hesablanır və təxmini xarakter daşıyır.
      </p>
    </section>
  );
}
