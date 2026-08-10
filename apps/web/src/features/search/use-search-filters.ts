"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import type {
  BuildingType,
  DealType,
  PropertyType,
  RepairStatus,
  SortKey
} from "@yenimenzil/types";
import { normalizeAz } from "@/services/listings-service";

export type ViewMode = "list" | "grid" | "map";

export interface UrlFilters {
  deal: DealType;
  district: string;
  propertyType: PropertyType | "all";
  rooms: number[];
  minPrice?: number;
  maxPrice?: number;
  minArea?: number;
  maxArea?: number;
  metro: string;
  buildingType?: BuildingType;
  repairStatus?: RepairStatus;
  ownerOnly: boolean;
  verifiedOnly: boolean;
  sort: SortKey;
}

export function parseRoomParam(value: string): number[] {
  return value
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean)
    .map((v) => (v === "4plus" ? 4 : Number(v)))
    .filter((v) => !Number.isNaN(v) && v >= 1 && v <= 4);
}

export function useSearchFilters() {
  const router = useRouter();
  const params = useSearchParams();

  const filters = React.useMemo<UrlFilters>(() => {
    const dealRaw = params.get("deal");
    const deal: DealType =
      dealRaw === "rent" || dealRaw === "daily" ? dealRaw : "sale";
    const propertyTypeRaw = params.get("property_type");
    const typeLabel = params.get("type");
    const district = params.get("district") ?? typeLabel ?? "";

    const parseNumber = (key: string): number | undefined => {
      const raw = params.get(key);
      if (!raw) return undefined;
      const n = Number(raw);
      return Number.isFinite(n) && n > 0 ? n : undefined;
    };

    const sortRaw = params.get("sort");
    const sort: SortKey = [
      "newest",
      "price_asc",
      "price_desc",
      "area_asc",
      "area_desc"
    ].includes(sortRaw ?? "")
      ? (sortRaw as SortKey)
      : "newest";

    return {
      deal,
      district,
      propertyType:
        propertyTypeRaw && propertyTypeRaw !== "all"
          ? (propertyTypeRaw as PropertyType)
          : "all",
      rooms: parseRoomParam(params.get("rooms") ?? ""),
      minPrice: parseNumber("min_price"),
      maxPrice: parseNumber("max_price"),
      minArea: parseNumber("min_area"),
      maxArea: parseNumber("max_area"),
      metro: params.get("metro") ?? "",
      buildingType: (params.get("building_type") as BuildingType) || undefined,
      repairStatus:
        (params.get("repair_status") as RepairStatus) || undefined,
      ownerOnly: params.get("owner_only") === "1",
      verifiedOnly: params.get("verified_only") === "1",
      sort
    };
  }, [params]);

  const push = React.useCallback(
    (updates: Record<string, string | number | undefined>) => {
      const next = new URLSearchParams(params.toString());
      for (const [key, value] of Object.entries(updates)) {
        if (value === undefined || value === "" || value === "all") {
          next.delete(key);
        } else {
          next.set(key, String(value));
        }
      }
      router.replace(`/search?${next.toString()}`, { scroll: false });
    },
    [params, router]
  );

  const setFilter = React.useCallback(
    (updates: Partial<UrlFilters>) => {
      const next: Record<string, string | number | undefined> = {};
      if (updates.deal !== undefined) next.deal = updates.deal;
      if (updates.district !== undefined) next.district = updates.district;
      if (updates.propertyType !== undefined)
        next.property_type = updates.propertyType;
      if (updates.rooms !== undefined)
        next.rooms =
          updates.rooms.length > 0
            ? updates.rooms
                .map((r) => (r >= 4 ? "4plus" : String(r)))
                .join(",")
            : undefined;
      if (updates.minPrice !== undefined) next.min_price = updates.minPrice;
      if (updates.maxPrice !== undefined) next.max_price = updates.maxPrice;
      if (updates.minArea !== undefined) next.min_area = updates.minArea;
      if (updates.maxArea !== undefined) next.max_area = updates.maxArea;
      if (updates.metro !== undefined) next.metro = updates.metro;
      if (updates.buildingType !== undefined)
        next.building_type = updates.buildingType;
      if (updates.repairStatus !== undefined)
        next.repair_status = updates.repairStatus;
      if (updates.ownerOnly !== undefined)
        next.owner_only = updates.ownerOnly ? "1" : undefined;
      if (updates.verifiedOnly !== undefined)
        next.verified_only = updates.verifiedOnly ? "1" : undefined;
      if (updates.sort !== undefined) next.sort = updates.sort;
      push(next);
    },
    [push]
  );

  const resetAll = React.useCallback(() => {
    push({ deal: filters.deal });
  }, [push, filters.deal]);

  return { filters, setFilter, push, resetAll };
}

export function districtLabelToSlug(label: string): string {
  return normalizeAz(label).replace(/ /g, "-");
}
