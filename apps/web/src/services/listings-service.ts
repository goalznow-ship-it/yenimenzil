import type {
  Property,
  SearchFilters,
  SortKey
} from "@yenimenzil/types";
import { getDemoListings } from "@/data/listings";

const AZ_MAP: Record<string, string> = {
  ə: "e",
  ş: "s",
  ğ: "g",
  ç: "c",
  ö: "o",
  ü: "u",
  ı: "i",
  ĝ: "g",
  Ə: "E",
  Ş: "S",
  Ğ: "G",
  Ç: "C",
  Ö: "O",
  Ü: "U",
  İ: "I"
};

export function normalizeAz(value: string): string {
  return value
    .toLowerCase()
    .replace(/[əşğçöüıƏŞĞÇÖÜİ]/g, (ch) => AZ_MAP[ch] ?? ch);
}

const sorters: Record<SortKey, (a: Property, b: Property) => number> = {
  newest: (a, b) => +new Date(b.publishedAt) - +new Date(a.publishedAt),
  price_asc: (a, b) => a.price - b.price,
  price_desc: (a, b) => b.price - a.price,
  area_asc: (a, b) => a.areaTotal - b.areaTotal,
  area_desc: (a, b) => b.areaTotal - a.areaTotal
};

export function filterListings(
  filters: Partial<SearchFilters>,
  source: Property[] = getDemoListings()
): Property[] {
  const deal = filters.deal ?? "sale";

  return source.filter((p) => {
    if (p.dealType !== deal) return false;

    if (filters.city && filters.city !== "all") {
      if (p.location.city !== filters.city) return false;
    }
    if (filters.district && filters.district !== "all") {
      const d = normalizeAz(filters.district);
      const match =
        normalizeAz(p.location.district).includes(d) ||
        normalizeAz(p.location.neighborhood ?? "").includes(d) ||
        normalizeAz(p.location.settlement ?? "").includes(d);
      if (!match) return false;
    }
    if (filters.propertyType && filters.propertyType !== "all") {
      if (p.propertyType !== filters.propertyType) return false;
    }
    if (filters.rooms && filters.rooms.length > 0) {
      const matches = filters.rooms.some((r) => {
        if (r === 0) return p.rooms === 0;
        if (r >= 4) return p.rooms >= 4;
        return p.rooms === r;
      });
      if (!matches) return false;
    }
    if (filters.minPrice != null && p.price < filters.minPrice) return false;
    if (filters.maxPrice != null && p.price > filters.maxPrice) return false;
    if (filters.minArea != null && p.areaTotal < filters.minArea) return false;
    if (filters.maxArea != null && p.areaTotal > filters.maxArea) return false;
    if (filters.metro && p.location.metro !== filters.metro) return false;
    if (filters.buildingType && p.buildingType !== filters.buildingType)
      return false;
    if (filters.repairStatus && p.repairStatus !== filters.repairStatus)
      return false;
    if (filters.ownerOnly && p.seller.kind !== "owner") return false;
    if (filters.verifiedOnly && !p.isVerified) return false;

    return true;
  });
}

export function sortListings(
  listings: Property[],
  sort: SortKey = "newest"
): Property[] {
  return [...listings].sort(sorters[sort]);
}

export function searchListings(
  filters: Partial<SearchFilters>
): Property[] {
  return sortListings(filterListings(filters), filters.sort ?? "newest");
}

export function getListingById(
  id: string,
  source: Property[] = getDemoListings()
): Property | undefined {
  return source.find((p) => p.id === id);
}

export function getSimilarListings(
  listing: Property,
  limit = 4,
  source: Property[] = getDemoListings()
): Property[] {
  return source
    .filter(
      (p) =>
        p.id !== listing.id &&
        p.dealType === listing.dealType &&
        p.propertyType === listing.propertyType
    )
    .sort((a, b) => Math.abs(a.price - listing.price) - Math.abs(b.price - listing.price))
    .slice(0, limit);
}

export function getPremiumListings(limit = 8): Property[] {
  return getDemoListings()
    .filter((p) => p.isPremium || p.isPromoted)
    .slice(0, limit);
}

export function getFeaturedSections() {
  const all = getDemoListings();
  return {
    newest: [...all].sort(
      (a, b) => +new Date(b.publishedAt) - +new Date(a.publishedAt)
    ),
    premium: all.filter((p) => p.isPremium || p.isPromoted),
    priceDropped: all.filter((p) => p.priceHistory.length >= 2),
    popular: all
      .filter((p) => p.views > 300)
      .sort((a, b) => b.views - a.views)
      .slice(0, 8),
    newBuildings: all.filter(
      (p) => p.propertyType === "new_building" && p.dealType === "sale"
    ),
    nearMetro: all.filter((p) => p.location.metro),
    seaside: all.filter(
      (p) =>
        p.location.district === "Xəzər" ||
        p.location.district === "Səbail"
    ),
    family: all.filter((p) => p.rooms >= 3 && p.dealType === "sale"),
    villas: all.filter((p) => p.propertyType === "villa"),
    land: all.filter((p) => p.propertyType === "land"),
    commercial: all.filter(
      (p) =>
        p.propertyType === "office" ||
        p.propertyType === "commercial" ||
        p.propertyType === "garage"
    )
  };
}
