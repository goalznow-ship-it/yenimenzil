import type { Property } from "@yenimenzil/types";
import Link from "next/link";
import { Camera, Heart, BedDouble, Ruler, Scale } from "lucide-react";
import { cn } from "@yenimenzil/ui";
import { formatPricePerSqm, formatPriceWithPeriod, timeAgo } from "@/lib/format";
import { useFavoritesStore } from "@/stores/favorites-store";
import { useComparisonStore } from "@/stores/comparison-store";
import { ImageWithFallback } from "@/components/common/image-with-fallback";
import { PropertyBadge } from "../properties/property-badge";

export function PropertyListRow({ property }: { property: Property }) {
  const has = useFavoritesStore((s) => s.has(property.id));
  const toggle = useFavoritesStore((s) => s.toggle);
  const inCompare = useComparisonStore((s) => s.has(property.id));
  const toggleCompare = useComparisonStore((s) => s.toggle);
  const hero = property.images[0];
  const hasPriceDrop =
    property.priceHistory.length >= 2 &&
    property.priceHistory.at(-1)!.price < property.priceHistory[0]!.price;

  return (
    <Link
      href={`/property/${property.id}`}
      className="group flex gap-4 rounded-2xl bg-surface p-3 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card hover:ring-brand/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40"
    >
      <div className="relative h-40 w-44 shrink-0 overflow-hidden rounded-xl bg-foreground/[0.03] sm:h-44 sm:w-56">
        {hero ? (
          <ImageWithFallback
            src={hero.src}
            alt={hero.alt}
            fill
            sizes="240px"
            placeholder="blur"
            blurDataURL={hero.placeholder}
            className="object-cover transition-transform duration-300 ease-out group-hover:scale-[1.03]"
          />
        ) : null}
        <div className="absolute left-2 top-2 flex flex-wrap gap-1">
          {property.isPremium ? <PropertyBadge kind="premium" /> : null}
          {property.isPromoted ? <PropertyBadge kind="promoted" /> : null}
          {hasPriceDrop ? <PropertyBadge kind="price_drop" /> : null}
        </div>
        {property.images.length > 1 ? (
          <span className="absolute bottom-2 right-2 flex items-center gap-1 rounded-full bg-black/45 px-2 py-0.5 text-[11px] font-medium text-white backdrop-blur-sm">
            <Camera className="h-3 w-3" />
            {property.images.length}
          </span>
        ) : null}
      </div>

      <div className="flex min-w-0 flex-1 flex-col py-0.5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-semibold tabular-nums tracking-tight text-foreground">
                {formatPriceWithPeriod(property.price, property.dealType)}
              </span>
              {property.pricePerSqm ? (
                <span className="text-xs text-muted-foreground">
                  {formatPricePerSqm(property.pricePerSqm)}
                </span>
              ) : null}
            </div>
            <p className="mt-0.5 line-clamp-1 text-[13px] text-muted-foreground">
              {property.title}
            </p>
            <p className="mt-1 line-clamp-1 text-[13px] text-foreground/80">
              {property.location.addressText}
            </p>
          </div>
          <button
            type="button"
            aria-label={inCompare ? "Müqayisədən sil" : "Müqayisəyə əlavə et"}
            aria-pressed={inCompare}
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              toggleCompare(property.id);
            }}
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/95 shadow-[0_2px_8px_rgba(20,23,22,0.12)] ring-1 ring-black/5 transition-all duration-150 hover:scale-110 hover:text-foreground active:scale-95",
              inCompare && "bg-brand/10 ring-brand/30 text-brand"
            )}
          >
            <Scale className="h-[18px] w-[18px]" strokeWidth={2} />
          </button>
          <button
            type="button"
            aria-label={has ? "Seçilmişlərdən sil" : "Seçilmişlərə əlavə et"}
            aria-pressed={has}
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              toggle(property.id);
            }}
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/95 shadow-[0_2px_8px_rgba(20,23,22,0.12)] ring-1 ring-black/5 transition-all duration-150 hover:scale-110 hover:text-foreground active:scale-95",
              has && "bg-red-50 ring-red-200 text-red-500"
            )}
          >
            <Heart
              className="h-[18px] w-[18px]"
              fill={has ? "currentColor" : "none"}
              strokeWidth={2}
            />
          </button>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[13px] text-foreground/75">
          {property.rooms > 0 ? (
            <span className="flex items-center gap-1.5">
              <BedDouble className="h-4 w-4 text-foreground/40" />
              {property.rooms} otaq
            </span>
          ) : null}
          <span className="flex items-center gap-1.5">
            <Ruler className="h-4 w-4 text-foreground/40" />
            {property.areaTotal} m²
          </span>
          {property.floor != null && property.floor > 0 ? (
            <span>
              {property.floor}/{property.totalFloors} mərtəbə
            </span>
          ) : null}
          {property.location.metro ? (
            <span className="flex items-center gap-1 text-brand">
              <span className="h-1.5 w-1.5 rounded-full bg-brand" />
              {property.location.metro}
            </span>
          ) : null}
        </div>

        <div className="mt-auto flex items-center justify-between pt-2 text-xs text-muted-foreground">
          <span>{timeAgo(property.publishedAt)}</span>
          <span>
            {property.seller.kind === "owner"
              ? "Mülkiyyətçi"
              : property.seller.agencyName ?? "Agentlik"}
          </span>
        </div>
      </div>
    </Link>
  );
}
