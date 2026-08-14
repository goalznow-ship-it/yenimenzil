"use client";

import * as React from "react";
import Link from "next/link";
import { MapPin, ArrowRight } from "lucide-react";
import { MapView } from "@/features/map/map-view";
import { searchProperties } from "@/services/property-api";
import type { MapMarkerData } from "@/lib/map/types";
import { formatPriceShort } from "@/lib/format";
import { useI18n } from "@/components/i18n-provider";

export function MapDiscover() {
  const { t } = useI18n();
  const [markers, setMarkers] = React.useState<MapMarkerData[]>([]);

  React.useEffect(() => {
    let cancelled = false;
    searchProperties({ deal: "sale", sort: "newest" })
      .then((res) => {
        if (cancelled) return;
        setMarkers(
          res.data
            .filter((p) => p.dealType === "sale")
            .map((p) => ({
              id: p.id,
              point: p.location.point,
              price: p.price,
              formattedPrice: formatPriceShort(p.price)
            }))
        );
      })
      .catch(() => {
        if (cancelled) return;
        setMarkers([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section aria-labelledby="map-discover-title" className="relative">
      <div className="relative h-[420px] overflow-hidden rounded-3xl ring-1 ring-border/70">
        <MapView markers={markers} center={{ lat: 40.452, lng: 49.88 }} zoom={10.5} />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-background/80 via-transparent to-transparent" />
        <div className="pointer-events-none absolute inset-x-0 top-0 flex justify-center p-4">
          <div className="pointer-events-auto rounded-full border border-border/70 bg-surface/95 px-5 py-2.5 shadow-card backdrop-blur-sm">
            <h2 id="map-discover-title" className="flex items-center gap-2 text-[15px] font-semibold text-foreground">
              <MapPin className="h-4 w-4 text-brand" />
              {t("map.discover")}
            </h2>
          </div>
        </div>
        <Link
          href="/map"
          className="absolute bottom-6 left-1/2 -translate-x-1/2 rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-brand/25 transition-all hover:bg-brand-hover hover:shadow-xl active:scale-95"
        >
          <span className="flex items-center gap-2">
            {t("map.viewAll")}
            <ArrowRight className="h-4 w-4" />
          </span>
        </Link>
      </div>
    </section>
  );
}
