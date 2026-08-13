"use client";

import * as React from "react";
import Link from "next/link";
import type { Property } from "@yenimenzil/types";
import { BUILDING_TYPE_LABELS, PROPERTY_TYPE_LABELS, REPAIR_LABELS } from "@yenimenzil/types";
import { useComparisonStore } from "@/stores/comparison-store";
import { fetchPropertyById } from "@/services/property-api";
import { EmptyState, Skeleton } from "@yenimenzil/ui";
import { Scale, Trash2, ArrowLeft } from "lucide-react";
import { formatPriceWithPeriod, formatPricePerSqm, areaLabel } from "@/lib/format";

interface Row {
  label: string;
  value: (p: Property) => string;
}

const ROWS: Row[] = [
  { label: "Qiymət", value: (p) => formatPriceWithPeriod(p.price, p.dealType) },
  { label: "Qiymət / m²", value: (p) => (p.pricePerSqm ? formatPricePerSqm(p.pricePerSqm) : "—") },
  { label: "Əmlak növü", value: (p) => PROPERTY_TYPE_LABELS[p.propertyType] },
  {
    label: "Tikili növü",
    value: (p) => (p.buildingType ? BUILDING_TYPE_LABELS[p.buildingType] : "—")
  },
  { label: "Otaqlar", value: (p) => (p.rooms > 0 ? String(p.rooms) : "—") },
  { label: "Yataq otağı", value: (p) => (p.bedrooms ? String(p.bedrooms) : "—") },
  { label: "Sanitar qovşağı", value: (p) => (p.bathrooms ? String(p.bathrooms) : "—") },
  { label: "Ümumi sahə", value: (p) => areaLabel(p.areaTotal) },
  {
    label: "Yaşayış sahəsi",
    value: (p) => (p.areaLiving ? areaLabel(p.areaLiving) : "—")
  },
  { label: "Torpaq sahəsi", value: (p) => (p.areaLand ? areaLabel(p.areaLand) : "—") },
  {
    label: "Mərtəbə",
    value: (p) =>
      p.floor != null && p.floor > 0 ? `${p.floor} / ${p.totalFloors}` : "—"
  },
  {
    label: "Təmir",
    value: (p) => (p.repairStatus ? REPAIR_LABELS[p.repairStatus] ?? p.repairStatus : "—")
  },
  {
    label: "Metro",
    value: (p) => p.location.metro ?? "—"
  },
  {
    label: "Ünvan",
    value: (p) => p.location.addressText
  }
];

export function ComparePage() {
  const ids = useComparisonStore((s) => s.ids);
  const remove = useComparisonStore((s) => s.remove);
  const clear = useComparisonStore((s) => s.clear);
  const [listings, setListings] = React.useState<Property[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let cancelled = false;
    if (ids.length === 0) {
      return;
    }
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
        icon={<Scale className="h-7 w-7" />}
        title="Müqayisə üçün elan seçilməyib"
        description="Elan kartlarında müqayisə işarəsinə klikləyin — 4 elana qədər müqayisə edə bilərsiniz."
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

  if (loading) {
    return (
      <div className="grid gap-4 lg:grid-cols-[160px_1fr_1fr_1fr_1fr]">
        {Array.from({ length: 16 }).map((_, i) => (
          <Skeleton key={i} className="h-10" />
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Müqayisə</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {listings.length} elan müqayisə edilir
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clear}
            className="inline-flex items-center gap-1.5 rounded-xl bg-foreground/[0.05] px-3.5 py-2 text-[13px] font-medium text-foreground/80 transition-colors hover:bg-foreground/[0.09]"
          >
            <Trash2 className="h-4 w-4" />
            Təmizlə
          </button>
        </div>
      </div>

      <div className="mt-6 overflow-x-auto rounded-2xl bg-surface ring-1 ring-border/70">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead>
            <tr>
              <th className="w-36 border-b border-border/70 p-3 text-left align-bottom text-xs font-medium uppercase tracking-wide text-muted-foreground" />
              {listings.map((p) => (
                <th key={p.id} className="min-w-[180px] border-b border-border/70 p-3 align-top">
                  <div className="relative">
                    <button
                      onClick={() => remove(p.id)}
                      aria-label="Müqayisədən çıxar"
                      className="absolute right-0 top-0 rounded-lg p-1 text-foreground/40 transition-colors hover:bg-red-500/10 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                    <div className="h-24 w-full overflow-hidden rounded-xl bg-foreground/[0.03]">
                      {p.images[0] ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={p.images[0].src}
                          alt={p.images[0].alt}
                          className="h-full w-full object-cover"
                        />
                      ) : null}
                    </div>
                    <p className="mt-2 line-clamp-2 font-medium leading-snug text-foreground">
                      {p.title}
                    </p>
                    <p className="mt-1 line-clamp-1 text-xs text-muted-foreground">
                      {p.location.addressText}
                    </p>
                    <Link
                      href={`/property/${p.id}`}
                      className="mt-2 inline-flex text-[13px] font-semibold text-brand transition-colors hover:text-brand-hover"
                    >
                      Ətraflı bax
                    </Link>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.label} className="odd:bg-foreground/[0.015]">
                <td className="border-b border-border/50 p-3 text-[13px] font-medium text-foreground/70">
                  {row.label}
                </td>
                {listings.map((p) => (
                  <td key={p.id} className="border-b border-border/50 p-3 text-[13.5px] text-foreground">
                    {row.value(p)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Link
        href="/search"
        className="mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-brand"
      >
        <ArrowLeft className="h-4 w-4" />
        Axtarışa qayıt
      </Link>
    </div>
  );
}
