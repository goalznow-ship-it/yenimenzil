"use client";

import Link from "next/link";
import type { Property } from "@yenimenzil/types";
import { PROPERTY_TYPE_LABELS } from "@yenimenzil/types";
import { cn } from "@yenimenzil/ui";
import { Camera, Heart, Ruler, Scale } from "lucide-react";
import {
  formatPricePerSqm,
  formatPriceWithPeriod,
  timeAgo
} from "@/lib/format";
import { useFavoritesStore } from "@/stores/favorites-store";
import { useComparisonStore } from "@/stores/comparison-store";
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

function CompareButton({ property }: { property: Property }) {
  const has = useComparisonStore((s) => s.has(property.id));
  const toggle = useComparisonStore((s) => s.toggle);
  const atLimit = useComparisonStore((s) => s.atLimit());

  return (
    <button
      type="button"
      aria-label={has ? "Müqayisədən sil" : "Müqayisəyə əlavə et"}
      aria-pressed={has}
      title={atLimit && !has ? "Maksimum 4 elan müqayisə edilə bilər" : undefined}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        toggle(property.id);
      }}
      className={cn(
        "flex h-9 w-9 items-center justify-center rounded-full bg-white/95 shadow-[0_2px_8px_rgba(20,23,22,0.16)] ring-1 ring-black/5 transition-all duration-150 hover:scale-110 active:scale-95",
        has && "bg-brand/10 ring-brand/30"
      )}
    >
      <Scale
        className={cn(
          "h-[17px] w-[17px]",
          has ? "text-brand" : "text-foreground/70"
        )}
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
        "group block overflow-hidden rounded-2xl bg-surface shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:ring-brand/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40",
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
            className="object-cover transition-transform duration-500 ease-out group-hover:scale-[1.03]"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-brand/5 to-brand/10">
            <svg className="h-16 w-16 text-brand/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}

        <div className="absolute left-3 top-3 flex flex-wrap items-center gap-1.5">
          {property.isPremium ? <PropertyBadge kind="premium" /> : null}
          {property.isPromoted ? <PropertyBadge kind="promoted" /> : null}
          {hasPriceDrop ? <PropertyBadge kind="price_drop" /> : null}
          {property.badges.includes("new") ? <PropertyBadge kind="new" /> : null}
        </div>

        <div className="absolute right-3 top-3 flex flex-col items-end gap-2">
          <FavoriteButton property={property} />
          <CompareButton property={property} />
        </div>

        {property.images.length > 1 ? (
          <span className="absolute bottom-3 right-3 flex items-center gap-1 rounded-full bg-black/50 px-3 py-1.5 text-[11px] font-medium text-white backdrop-blur-sm">
            <Camera className="h-3.5 w-3.5" />
            {property.images.length}
          </span>
        ) : null}

        <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/40 via-black/10 to-transparent" />
      </div>

      <div className={cn("p-4 pb-3", compact ? "pt-2" : "pt-2")}>
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-[20px] font-bold tabular-nums tracking-tight text-foreground">
            {formatPriceWithPeriod(property.price, property.dealType)}
          </span>
          {property.pricePerSqm ? (
            <span className="shrink-0 text-xs font-medium tabular-nums text-muted-foreground bg-brand/10 text-brand px-2 py-0.5 rounded-full">
              {formatPricePerSqm(property.pricePerSqm)}
            </span>
          ) : null}
        </div>

        <h3 className="mt-2 line-clamp-1 text-[15px] font-semibold text-foreground leading-snug">
          {titleFor(property)}
        </h3>

        <p className="mt-1 line-clamp-1 text-[13px] text-muted-foreground">
          {property.location.addressText}
        </p>

        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[13px] text-foreground/70">
          {property.rooms > 0 ? (
            <span className="flex items-center gap-1.5 text-foreground/75">
              <span className="relative flex h-5 w-5 items-center justify-center">
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 22V9l9-7 9 7" />
                </svg>
              </span>
              {property.rooms} otaq
            </span>
          ) : null}
          <span className="flex items-center gap-1.5 text-foreground/75">
            <Ruler className="h-4 w-4 text-foreground/40" />
            {property.areaTotal} m²
          </span>
          {property.floor != null && property.floor > 0 ? (
            <span className="flex items-center gap-1.5 text-foreground/75">
              <span className="relative flex h-5 w-5 items-center justify-center">
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </span>
              {property.floor}/{property.totalFloors} mərtəbə
            </span>
          ) : null}
          {property.location.metro ? (
            <span className="ml-auto flex items-center gap-1.5 rounded-full bg-brand/10 text-brand px-2.5 py-1 text-xs font-medium">
              <span className="h-1.5 w-1.5 rounded-full bg-brand" />
              {property.location.metro}
            </span>
          ) : null}
        </div>

        <div className="mt-3 flex items-center justify-between border-t border-border/60 pt-3">
          <span className="text-xs text-muted-foreground">
            {timeAgo(property.publishedAt)}
          </span>
          <span className="flex items-center gap-1.5 text-xs font-medium text-foreground/70">
            {property.seller.kind === "owner" ? (
              <>
                <svg className="h-3.5 w-3.5 text-foreground/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h18a7 7 0 00-7-7z" />
                </svg>
                Mülkiyyətçi
              </>
            ) : (
              <>
                <svg className="h-3.5 w-3.5 text-foreground/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                {property.seller.agencyName ?? "Agentlik"}
              </>
            )}
          </span>
        </div>
      </div>
    </Link>
  );
}