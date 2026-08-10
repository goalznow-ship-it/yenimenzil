import { getDemoListings } from "@/data/listings";

export interface PopularArea {
  name: string;
  href: string;
  count: number;
}

const all = getDemoListings();

function countFor(query: string, value: string): number {
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

export const DISTRICT_POPULAR_AREAS: PopularArea[] = [
  {
    name: "Nərimanov",
    href: "/search?deal=sale&district=nerimanov",
    count: countFor("district", "Nərimanov")
  },
  {
    name: "Yasamal",
    href: "/search?deal=sale&district=yasamal",
    count: countFor("district", "Yasamal")
  },
  {
    name: "Səbail",
    href: "/search?deal=sale&district=sebail",
    count: countFor("district", "Səbail")
  },
  {
    name: "Nəsimi",
    href: "/search?deal=sale&district=nesimi",
    count: countFor("district", "Nəsimi")
  },
  {
    name: "Xətai",
    href: "/search?deal=sale&district=xetai",
    count: countFor("district", "Xətai")
  },
  {
    name: "Mərdəkan",
    href: "/search?deal=sale&district=merdekan",
    count: countFor("settlement", "Mərdəkan")
  },
  {
    name: "Şüvəlan",
    href: "/search?deal=sale&district=suvelan",
    count: countFor("settlement", "Şüvəlan")
  },
  {
    name: "Sumqayıt",
    href: "/search?deal=sale&district=sumqayit",
    count: all.filter((p) => p.location.city === "Sumqayıt").length
  }
];
