"use client";

import * as React from "react";
import type { Property } from "@yenimenzil/types";
import { formatPrice } from "@/lib/format";
import { cn } from "@yenimenzil/ui";
import { TrendingDown, TrendingUp, Info } from "lucide-react";

export function PriceHistoryCard({ property }: { property: Property }) {
  const history = property.priceHistory;
  if (history.length === 0) return null;

  const initial = history[0]!.price;
  const latest = property.price;
  const dropped = latest < initial;
  const diff = Math.abs(initial - latest);

  const rows = [...history]
    .sort((a, b) => +new Date(a.date) - +new Date(b.date))
    .map((entry) => ({
      ...entry,
      date: new Date(entry.date).toLocaleDateString("az-AZ", {
        day: "numeric",
        month: "long"
      })
    }));

  return (
    <section
      aria-labelledby="price-history-title"
      className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70"
    >
      <h2
        id="price-history-title"
        className="text-base font-semibold text-foreground"
      >
        Qiymət tarixçəsi
      </h2>

      {dropped ? (
        <p className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-[13px] font-medium text-emerald-800 ring-1 ring-emerald-100">
          <TrendingDown className="h-4 w-4" />
          Qiymət {formatPrice(diff)} endirilib
        </p>
      ) : latest > initial ? (
        <p className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-[13px] font-medium text-amber-800 ring-1 ring-amber-100">
          <TrendingUp className="h-4 w-4" />
          Qiymət {formatPrice(diff)} artırılıb
        </p>
      ) : null}

      <ul className="mt-4 space-y-2.5">
        {rows.map((row, i) => {
          const isLast = i === rows.length - 1;
          return (
            <li
              key={row.date + row.price}
              className="flex items-center justify-between text-sm"
            >
              <span className="text-muted-foreground">{row.date}</span>
              <span
                className={cn(
                  "font-semibold",
                  isLast ? "text-foreground" : "text-foreground/60"
                )}
              >
                {formatPrice(row.price)}
                {isLast ? " (hazırki)" : ""}
              </span>
            </li>
          );
        })}
      </ul>

      <p className="mt-4 flex items-center gap-1.5 text-[11px] text-foreground/40">
        <Info className="h-3.5 w-3.5" />
        Demo məlumatları — real tarixçə API ilə birlikdə aktivləşəcək.
      </p>
    </section>
  );
}
