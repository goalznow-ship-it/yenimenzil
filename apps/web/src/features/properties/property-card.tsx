"use client";

import Link from "next/link";
import type { Property } from "@yenimenzil/types";
import { PROPERTY_TYPE_LABELS } from "@yenimenzil/types";
import { cn } from "@yenimenzil/ui";
import { Camera, Heart, Ruler } from "lucide-react";
import {
  formatPricePerSqm,
  formatPriceWithPeriod,
  timeAgo
} from "@/lib/format";
import { useFavoritesStore } from "@/stores/favorites-store";
import { ImageWithFallback } from "@/components/common/image-with-fallback";
import { PropertyBadge } from "./property-badge";

export function dealLabel(p: Property): string {
  switch (p.dealType) {
    case "rent":
      return "Kirayə";
    case "daily":
      return "Günlük kirayə";
    default:
      return PROPERTY_TYPE_LABELS[p.propertyType];
  }
}

function titleFor(p: Property): string {
  if (p.dealType === "sale" && p.rooms > 0) {
    const type =
      p.propertyType === "new_building" ? "yeni tikili" : "mənzil";
    return `${p.rooms} otaqlı ${type}, ${p.areaTotal} m²`;
  }
  return p.title;
}

function FavoriteButton({ property }: { property: Property }) {
  const has = useFavoritesStore((s) => s.has(property.id));
  const toggle = useFavoritesStore((s) => s.toggle);

  return (
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
        "flex h-9 w-9 items-center justify-center rounded-full bg-white/95 shadow-[0_2px_8px_rgba(20,23,22,0.16)] ring-1 ring-black/5 transition-all duration-150 hover:scale-110 active:scale-95",
        has && "bg-red-50 ring-red-200"
      )}
    >
      <Heart
        className={cn(
          "h-[17px] w-[17px] transition-transform",
          has ? "scale-110 text-red-500" : "text-foreground/70"
        )}
        fill={has ? "currentColor" : "none"}
        strokeWidth={2}
      />
    </button>
  );
}

interface PropertyCardProps {
  property: Property;
  className?: string;
  compact?: boolean;
}

export function PropertyCard({ property, className, compact }: PropertyCardProps) {
  const hasPriceDrop =
    property.priceHistory.length >= 2 &&
    property.priceHistory.at(-1)!.price < property.priceHistory[0]!.price;
  const hero = property.images[0];

  return (
    <Link
      href={`/property/${property.id}`}
      className={cn(
        "group block overflow-hidden rounded-2xl bg-surface shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70 transition-all duration-200 hover:-translate-y-1 hover:shadow-card hover:ring-brand/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40",
        className
      )}
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-foreground/[0.03]">
        {hero ? (
          <ImageWithFallback
            src={hero.src}
            alt={hero.alt}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            placeholder="blur"
            blurDataURL={hero.placeholder}
            className="object-cover transition-transform duration-500 ease-out group-hover:scale-[1.04]"
          />
        ) : null}

        <div className="absolute left-2.5 top-2.5 flex flex-wrap items-center gap-1.5">
          {property.isPremium ? <PropertyBadge kind="premium" /> : null}
          {property.isPromoted ? <PropertyBadge kind="promoted" /> : null}
          {hasPriceDrop ? <PropertyBadge kind="price_drop" /> : null}
          {property.badges.includes("new") ? <PropertyBadge kind="new" /> : null}
        </div>

        <div className="absolute right-2.5 top-2.5">
          <FavoriteButton property={property} />
        </div>

        {property.images.length > 1 ? (
          <span className="absolute bottom-2.5 right-2.5 flex items-center gap-1 rounded-full bg-black/45 px-2.5 py-1 text-[11px] font-medium text-white backdrop-blur-sm">
            <Camera className="h-3.5 w-3.5" />
            {property.images.length}
          </span>
        ) : null}

        <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-black/30 to-transparent" />
      </div>

      <div className={cn("px-3 pb-3", compact ? "pt-2.5" : "pt-3")}>
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-[18px] font-semibold tabular-nums tracking-tight text-foreground">
            {formatPriceWithPeriod(property.price, property.dealType)}
          </span>
          {property.pricePerSqm ? (
            <span className="shrink-0 text-xs font-medium tabular-nums text-muted-foreground">
              {formatPricePerSqm(property.pricePerSqm)}
            </span>
          ) : null}
        </div>

        <h3 className="mt-1 line-clamp-1 text-[14.5px] font-medium text-foreground">
          {titleFor(property)}
        </h3>

        <p className="mt-0.5 line-clamp-1 text-[13px] text-muted-foreground">
          {property.location.addressText}
        </p>

        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[13px] text-foreground/75">
          {property.rooms > 0 ? (
            <span className="flex items-center gap-1.5">
              <span className="h-1 w-1 rounded-full bg-foreground/25" />
              {property.rooms} otaq
            </span>
          ) : null}
          <span className="flex items-center gap-1.5">
            <Ruler className="h-3.5 w-3.5 text-foreground/40" />
            {property.areaTotal} m²
          </span>
          {property.floor != null && property.floor > 0 ? (
            <span className="flex items-center gap-1.5">
              <span className="h-1 w-1 rounded-full bg-foreground/25" />
              {property.floor}/{property.totalFloors} mərtəbə
            </span>
          ) : null}
          {property.location.metro ? (
            <span className="ml-auto flex items-center gap-1 text-xs font-medium text-brand">
              <span className="h-1.5 w-1.5 rounded-full bg-brand" />
              {property.location.metro}
            </span>
          ) : null}
        </div>

        <div className="mt-2.5 flex items-center justify-between border-t border-border/80 pt-2">
          <span className="text-xs text-muted-foreground">
            {timeAgo(property.publishedAt)}
          </span>
          <span className="flex items-center gap-1.5 text-xs font-medium text-foreground/70">
            {property.seller.kind === "owner" ? (
              "Mülkiyyətçi"
            ) : (
              property.seller.agencyName ?? "Agentlik"
            )}
          </span>
        </div>
      </div>
    </Link>
  );
}
