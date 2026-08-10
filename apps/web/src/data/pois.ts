import type { GeoPoint } from "@yenimenzil/types";
import { distanceMeters } from "@/lib/geo";

interface Poi {
  name: string;
  kind: "metro" | "school" | "market" | "park" | "hospital";
  point: GeoPoint;
}

/**
 * Reference POIs for area intelligence. Coordinates are approximate,
 * distances are computed with haversine from the property location.
 */
export const REFERENCE_POIS: Poi[] = [
  { name: "Gənclik metrosu", kind: "metro", point: { lat: 40.4094, lng: 49.8503 } },
  { name: "Nəriman Nərimanov metrosu", kind: "metro", point: { lat: 40.4015, lng: 49.8664 } },
  { name: "28 May metrosu", kind: "metro", point: { lat: 40.3796, lng: 49.8462 } },
  { name: "İçərişəhər metrosu", kind: "metro", point: { lat: 40.3667, lng: 49.8322 } },
  { name: "Sahil metrosu", kind: "metro", point: { lat: 40.3705, lng: 49.846 } },
  { name: "Neftçilər metrosu", kind: "metro", point: { lat: 40.3708, lng: 49.855 } },
  { name: "İnşaatçılar metrosu", kind: "metro", point: { lat: 40.3893, lng: 49.8067 } },
  { name: "Elmlər Akademiyası metrosu", kind: "metro", point: { lat: 40.3842, lng: 49.8159 } },
  { name: "Azadlıq prospekti metrosu", kind: "metro", point: { lat: 40.4284, lng: 49.8218 } },
  { name: "Dərnəgül metrosu", kind: "metro", point: { lat: 40.4475, lng: 49.8372 } },
  { name: "İnternat məktəbi", kind: "school", point: { lat: 40.4099, lng: 49.855 } },
  { name: "№ 34 məktəb", kind: "school", point: { lat: 40.3839, lng: 49.8153 } },
  { name: "№ 200 məktəb", kind: "school", point: { lat: 40.4067, lng: 49.8514 } },
  { name: "№ 150 məktəb", kind: "school", point: { lat: 40.3719, lng: 49.8561 } },
  { name: "Neptun supermarketi", kind: "market", point: { lat: 40.4092, lng: 49.8484 } },
  { name: "Araz supermarketi", kind: "market", point: { lat: 40.3901, lng: 49.8144 } },
  { name: "Bravo supermarketi", kind: "market", point: { lat: 40.3722, lng: 49.8544 } },
  { name: "Dənizkənarı Milli Park", kind: "park", point: { lat: 40.3604, lng: 49.8339 } },
  { name: "Sahil bağı", kind: "park", point: { lat: 40.3683, lng: 49.8471 } },
  { name: "Hüseyn Cavid parkı", kind: "park", point: { lat: 40.3824, lng: 49.8188 } },
  { name: "Respublika Kliniki Xəstəxanası", kind: "hospital", point: { lat: 40.4079, lng: 49.8587 } },
  { name: "Mərkəzi Kliniki Xəstəxana", kind: "hospital", point: { lat: 40.3861, lng: 49.8223 } },
  { name: "Sumqayıt Mərkəzi Parkı", kind: "park", point: { lat: 40.5887, lng: 49.6646 } }
];

export interface NearbyPlace {
  name: string;
  kind: Poi["kind"];
  distanceMeters: number;
}

export function nearestPlaces(
  point: GeoPoint,
  limit: number,
  kinds?: Poi["kind"][]
): NearbyPlace[] {
  return REFERENCE_POIS.filter((poi) => !kinds || kinds.includes(poi.kind))
    .map((poi) => ({
      name: poi.name,
      kind: poi.kind,
      distanceMeters: distanceMeters(point, poi.point)
    }))
    .sort((a, b) => a.distanceMeters - b.distanceMeters)
    .slice(0, limit);
}
