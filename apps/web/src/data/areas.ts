import { getDemoListings } from "@/data/listings";
import type { Property } from "@yenimenzil/types";

export interface PopularArea {
  name: string;
  href: string;
  count: number;
}

function countFor(all: Property[], query: string, value: string): number {
  return all.filter((p) => {
    switch (query) {
      case "district":
        return (
          p.location.district === value ||
          p.location.neighborhood === value ||
          p.location.settlement === value
        );
      case "settlement":
        return p.location.settlement === value;
      default:
        return false;
    }
  }).length;
}

const AREA_DEFS: Array<Omit<PopularArea, "count">> = [
  {
    name: "Nərimanov",
    href: "/search?deal=sale&district=nerimanov"
  },
  {
    name: "Yasamal",
    href: "/search?deal=sale&district=yasamal"
  },
  {
    name: "Səbail",
    href: "/search?deal=sale&district=sebail"
  },
  {
    name: "Nəsimi",
    href: "/search?deal=sale&district=nesimi"
  },
  {
    name: "Xətai",
    href: "/search?deal=sale&district=xetai"
  },
  {
    name: "Mərdəkan",
    href: "/search?deal=sale&district=merdekan"
  },
  {
    name: "Şüvəlan",
    href: "/search?deal=sale&district=suvelan"
  },
  {
    name: "Sumqayıt",
    href: "/search?deal=sale&district=sumqayit"
  }
];

/**
 * Popular areas with live listing counts. Pass the current listing set (e.g.
 * fetched from the API) so counts reflect real data; defaults to the bundled
 * demo listings.
 */
export function getPopularAreas(listings?: Property[]): PopularArea[] {
  const all = listings ?? getDemoListings();
  return AREA_DEFS.map((area) => ({
    ...area,
    count:
      area.name === "Sumqayıt"
        ? all.filter((p) => p.location.city === "Sumqayıt").length
        : area.name === "Mərdəkan" || area.name === "Şüvəlan"
          ? countFor(all, "settlement", area.name)
          : countFor(all, "district", area.name)
  }));
}

export const DISTRICT_POPULAR_AREAS: PopularArea[] = getPopularAreas();
