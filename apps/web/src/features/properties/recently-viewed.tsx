"use client";

import * as React from "react";
import type { Property } from "@yenimenzil/types";
import { useRecentlyViewedStore } from "@/stores/recently-viewed-store";
import { fetchPropertyById } from "@/services/property-api";
import { PropertyCard } from "@/features/properties/property-card";
import { SectionHeading, Skeleton } from "@yenimenzil/ui";

export function RecentlyViewedSection({ excludeId }: { excludeId?: string }) {
  const ids = useRecentlyViewedStore((s) => s.ids);
  const [listings, setListings] = React.useState<Property[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let cancelled = false;
    const visibleIds = excludeId ? ids.filter((id) => id !== excludeId) : ids;
    if (visibleIds.length === 0) {
      return;
    }
    Promise.all(visibleIds.slice(0, 8).map((id) => fetchPropertyById(id)))
      .then((found) => {
        if (cancelled) return;
        setListings(found.filter((p) => p != null));
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [ids, excludeId]);

  if (!loading && listings.length === 0) return null;

  return (
    <section aria-labelledby="recently-viewed-title" className="mt-12">
      <SectionHeading
        title="Son baxdıqlarınız"
        subtitle="Baxdığınız elanlar burada saxlanılır"
      />
      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="overflow-hidden rounded-2xl bg-surface ring-1 ring-border/70"
              >
                <Skeleton className="aspect-[4/3] w-full rounded-none" />
                <div className="space-y-2.5 p-3.5">
                  <Skeleton className="h-5 w-2/5" />
                  <Skeleton className="h-4 w-4/5" />
                </div>
              </div>
            ))
          : listings.map((listing) => (
              <PropertyCard key={listing.id} property={listing} />
            ))}
      </div>
    </section>
  );
}
