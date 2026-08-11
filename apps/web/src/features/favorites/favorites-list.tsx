"use client";

import * as React from "react";
import Link from "next/link";
import type { Property } from "@yenimenzil/types";
import { useFavoritesStore } from "@/stores/favorites-store";
import { fetchPropertyById } from "@/services/property-api";
import { PropertyCard } from "@/features/properties/property-card";
import { EmptyState, SectionHeading, Skeleton } from "@yenimenzil/ui";
import { Heart } from "lucide-react";

export function FavoritesList() {
  const ids = useFavoritesStore((s) => s.ids);
  const [listings, setListings] = React.useState<Property[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let cancelled = false;
    Promise.all(ids.map((id) => fetchPropertyById(id)))
      .then((found) => {
        if (cancelled) return;
        setListings(found.filter((p) => p != null));
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
  }, [ids]);

  if (ids.length === 0) {
    return (
      <EmptyState
        icon={<Heart className="h-7 w-7" />}
        title="Seçilmişlər boşdur"
        description="Elanlarda ürək işarəsinə klikləyin — seçdiyiniz elanlar burada toplanacaq."
        action={
          <Link
            href="/search"
            className="inline-flex h-11 items-center justify-center rounded-[10px] bg-brand px-6 text-sm font-medium text-white hover:bg-brand-hover"
          >
            Elanlara bax
          </Link>
        }
      />
    );
  }

  return (
    <div>
      <SectionHeading
        title={`Seçilmişlər (${listings.length})`}
        subtitle="Sizə uyğun elanları burada saxlayın"
      />
      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
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
          ))}
        </div>
      ) : listings.length === 0 ? (
        <div className="rounded-2xl bg-surface p-10 text-center ring-1 ring-border/70">
          <p className="text-sm text-muted-foreground">
            Seçilmiş elanlar artıq mövcud deyil və ya axtarışda tapılmadı.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {listings.map((listing) => (
            <PropertyCard key={listing.id} property={listing} />
          ))}
        </div>
      )}
    </div>
  );
}
