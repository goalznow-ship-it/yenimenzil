import type { Property } from "@yenimenzil/types";
import { PropertyCard } from "./property-card";
import { Skeleton } from "@yenimenzil/ui";

interface PropertyGridProps {
  listings: Property[];
  className?: string;
  columns?: 3 | 4;
}

export function PropertyGrid({
  listings,
  className,
  columns = 4
}: PropertyGridProps) {
  const gridClass =
    columns === 4
      ? "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
      : "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3";

  return (
    <div className={`${gridClass} ${className ?? ""}`}>
      {listings.map((listing) => (
        <PropertyCard key={listing.id} property={listing} />
      ))}
    </div>
  );
}

export function PropertyGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="overflow-hidden rounded-2xl bg-surface ring-1 ring-border/70">
          <Skeleton className="aspect-[4/3] w-full rounded-none" />
          <div className="space-y-2.5 p-3.5">
            <Skeleton className="h-5 w-2/5" />
            <Skeleton className="h-4 w-4/5" />
            <Skeleton className="h-3.5 w-3/5" />
          </div>
        </div>
      ))}
    </div>
  );
}
