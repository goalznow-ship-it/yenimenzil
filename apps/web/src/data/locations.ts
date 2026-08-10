import type { GeoPoint } from "@yenimenzil/types";

export interface LocationArea {
  city: string;
  citySlug: string;
  district: string;
  districtSlug: string;
  settlement?: string;
  neighborhood?: string;
  metro?: string;
  point: GeoPoint;
  popular: boolean;
}

export const CITIES = [
  { name: "Bakı", slug: "baki" },
  { name: "Sumqayıt", slug: "sumqayit" },
  { name: "Gəncə", slug: "gence" },
  { name: "Xırdalan", slug: "xirdalan" }
] as const;

export const DISTRICTS: LocationArea[] = [
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Nərimanov",
    districtSlug: "nerimanov",
    neighborhood: "Gənclik",
    metro: "Gənclik",
    point: { lat: 40.4086, lng: 49.8491 },
    popular: true
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Nərimanov",
    districtSlug: "nerimanov",
    neighborhood: "Nəriman Nərimanov",
    metro: "Nəriman Nərimanov",
    point: { lat: 40.4015, lng: 49.8664 },
    popular: true
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Yasamal",
    districtSlug: "yasamal",
    neighborhood: "İnşaatçılar",
    metro: "İnşaatçılar",
    point: { lat: 40.3893, lng: 49.8067 },
    popular: true
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Yasamal",
    districtSlug: "yasamal",
    neighborhood: "Elmlər Akademiyası",
    metro: "Elmlər Akademiyası",
    point: { lat: 40.3842, lng: 49.8159 },
    popular: false
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Nəsimi",
    districtSlug: "nesimi",
    neighborhood: "28 May",
    metro: "28 May",
    point: { lat: 40.3796, lng: 49.8462 },
    popular: true
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Nəsimi",
    districtSlug: "nesimi",
    neighborhood: "Koroğlu",
    metro: "Koroğlu",
    point: { lat: 40.4031, lng: 49.8096 },
    popular: false
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Xətai",
    districtSlug: "xetai",
    neighborhood: "Neftçilər",
    metro: "Neftçilər",
    point: { lat: 40.3708, lng: 49.855 },
    popular: true
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Xətai",
    districtSlug: "xetai",
    neighborhood: "Şəhriyar",
    metro: "Şəhriyar",
    point: { lat: 40.3698, lng: 49.847 },
    popular: false
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Səbail",
    districtSlug: "sebail",
    neighborhood: "İçərişəhər",
    metro: "İçərişəhər",
    point: { lat: 40.3667, lng: 49.8322 },
    popular: true
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Səbail",
    districtSlug: "sebail",
    neighborhood: "Sahil",
    metro: "Sahil",
    point: { lat: 40.3705, lng: 49.846 },
    popular: true
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Binəqədi",
    districtSlug: "bineqedi",
    neighborhood: "Azadlıq prospekti",
    metro: "Azadlıq prospekti",
    point: { lat: 40.4284, lng: 49.8218 },
    popular: true
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Binəqədi",
    districtSlug: "bineqedi",
    neighborhood: "Dərnəgül",
    metro: "Dərnəgül",
    point: { lat: 40.4475, lng: 49.8372 },
    popular: false
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Xəzər",
    districtSlug: "xezer",
    settlement: "Mərdəkan",
    point: { lat: 40.4925, lng: 50.1365 },
    popular: true
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Xəzər",
    districtSlug: "xezer",
    settlement: "Şüvəlan",
    point: { lat: 40.4547, lng: 50.2 },
    popular: true
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Xəzər",
    districtSlug: "xezer",
    settlement: "Buzovna",
    point: { lat: 40.516, lng: 50.116 },
    popular: true
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Xəzər",
    districtSlug: "xezer",
    settlement: "Bilgəh",
    point: { lat: 40.568, lng: 50.034 },
    popular: false
  },
  {
    city: "Bakı",
    citySlug: "baki",
    district: "Xəzər",
    districtSlug: "xezer",
    settlement: "Sea Breeze",
    point: { lat: 40.4928, lng: 50.0297 },
    popular: true
  },
  {
    city: "Xırdalan",
    citySlug: "xirdalan",
    district: "Abşeron",
    districtSlug: "abseron",
    point: { lat: 40.448, lng: 49.756 },
    popular: true
  },
  {
    city: "Sumqayıt",
    citySlug: "sumqayit",
    district: "Mərkəz",
    districtSlug: "sumqayit-merkez",
    point: { lat: 40.5855, lng: 49.6319 },
    popular: true
  },
  {
    city: "Sumqayıt",
    citySlug: "sumqayit",
    district: "Corat",
    districtSlug: "sumqayit-corat",
    point: { lat: 40.5803, lng: 49.703 },
    popular: false
  }
];

export const POPULAR_PLACES = [
  { label: "Bakı", district: "Bakı" },
  { label: "Nərimanov", district: "Nərimanov" },
  { label: "Yasamal", district: "Yasamal" },
  { label: "Nəsimi", district: "Nəsimi" },
  { label: "Xətai", district: "Xətai" },
  { label: "Səbail", district: "Səbail" },
  { label: "28 May", district: "28 May" },
  { label: "Gənclik", district: "Gənclik" },
  { label: "Mərdəkan", district: "Mərdəkan" },
  { label: "Şüvəlan", district: "Şüvəlan" },
  { label: "Xırdalan", district: "Xırdalan" },
  { label: "Sumqayıt", district: "Sumqayıt" }
] as const;

export function districtFromLabel(label: string): LocationArea | undefined {
  if (label === "Bakı") {
    return {
      city: "Bakı",
      citySlug: "baki",
      district: "Bakı",
      districtSlug: "baki",
      point: { lat: 40.4093, lng: 49.8671 },
      popular: true
    };
  }
  return DISTRICTS.find(
    (d) =>
      d.district === label ||
      d.neighborhood === label ||
      d.settlement === label
  );
}

export const METRO_STATIONS = [
  "Gənclik",
  "Nəriman Nərimanov",
  "28 May",
  "İçərişəhər",
  "Sahil",
  "Neftçilər",
  "Xətai",
  "Koroğlu",
  "Elmlər Akademiyası",
  "İnşaatçılar",
  "Memar Əcəmi",
  "Azadlıq prospekti",
  "Dərnəgül",
  "Bakıxanov",
  "Şəhriyar"
] as const;
