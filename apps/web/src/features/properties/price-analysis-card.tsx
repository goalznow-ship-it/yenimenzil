import type { Property } from "@yenimenzil/types";
import { TrendingDown, TrendingUp, Info } from "lucide-react";
import { getDemoListings } from "@/data/listings";
import { formatPrice, formatPricePerSqm } from "@/lib/format";
import { cn } from "@yenimenzil/ui";

/**
 * Price intelligence — estimates only.
 * Phase 1 uses demo listings to compute district medians; Phase 2 will use
 * real market data from the backend. Estimates are always labelled as such.
 */
export function PriceAnalysisCard({ property }: { property: Property }) {
  const pool = getDemoListings().filter(
    (p) =>
      p.id !== property.id &&
      p.dealType === property.dealType &&
      p.propertyType === property.propertyType &&
      p.pricePerSqm != null &&
      property.pricePerSqm != null
  );

  if (pool.length < 3 || !property.pricePerSqm) return null;

  const median = (values: number[]) => {
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0
      ? sorted[mid]!
      : (sorted[mid - 1]! + sorted[mid]!) / 2;
  };

  const districtMedian =
    median(
      pool
        .filter(
          (p) =>
            p.location.district === property.location.district ||
            p.location.settlement === property.location.settlement
        )
        .map((p) => p.pricePerSqm!)
    ) ?? median(pool.map((p) => p.pricePerSqm!));

  const deltaPercent =
    ((property.pricePerSqm - districtMedian) / districtMedian) * 100;
  const below = deltaPercent < 0;
  const abs = Math.abs(deltaPercent);
  const tone = abs < 3 ? "neutral" : below ? "good" : "attention";

  const rangeLow = Math.round(districtMedian * 0.92);
  const rangeHigh = Math.round(districtMedian * 1.08);

  return (
    <section
      aria-labelledby="price-analysis-title"
      className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70"
    >
      <div className="flex items-start justify-between gap-3">
        <h2
          id="price-analysis-title"
          className="text-base font-semibold text-foreground"
        >
          Qiymət analizi
        </h2>
        <span className="flex items-center gap-1 rounded-full bg-foreground/[0.05] px-2.5 py-1 text-[11px] text-foreground/60">
          <Info className="h-3 w-3" />
          Təxmini
        </span>
      </div>

      <div
        className={cn(
          "mt-3 flex items-start gap-3 rounded-xl p-3.5 ring-1 ring-black/[0.03]",
          tone === "good" && "bg-emerald-50",
          tone === "attention" && "bg-amber-50",
          tone === "neutral" && "bg-foreground/[0.03]"
        )}
      >
        {below ? (
          <TrendingDown className="mt-0.5 h-5 w-5 shrink-0 text-emerald-700" />
        ) : (
          <TrendingUp
            className={cn(
              "mt-0.5 h-5 w-5 shrink-0",
              tone === "attention" ? "text-amber-700" : "text-emerald-700"
            )}
          />
        )}
        <p className="text-sm leading-relaxed text-foreground/85">
          {below
            ? `Bu əmlak oxşar elanların orta qiymətindən təxminən ${abs.toFixed(0)}% aşağıdır.`
            : abs <= 3
              ? "Bu əmlakın qiyməti oxşar elanların orta qiymətinə uyğundur."
              : `Bu əmlak oxşar elanların orta qiymətindən təxminən ${abs.toFixed(0)}% bahadır.`}
        </p>
      </div>

      <dl className="mt-4 space-y-3 text-sm">
        <div className="flex items-center justify-between">
          <dt className="text-muted-foreground">Bu əmlak</dt>
          <dd className="font-semibold text-foreground">
            {formatPricePerSqm(property.pricePerSqm)}
          </dd>
        </div>
        <div className="flex items-center justify-between">
          <dt className="text-muted-foreground">
            Rayon üzrə median qiymət / m²
          </dt>
          <dd className="font-medium text-foreground">
            {formatPricePerSqm(districtMedian)}
          </dd>
        </div>
        <div className="flex items-center justify-between">
          <dt className="text-muted-foreground">Oxşar elanların diapazonu</dt>
          <dd className="font-medium text-foreground">
            {formatPrice(rangeLow)} — {formatPrice(rangeHigh)}
          </dd>
        </div>
      </dl>
    </section>
  );
}
