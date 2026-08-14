import type { Currency, DealType } from "@yenimenzil/types";

const AZN_GROUP_SEPARATOR = " ";

export function formatPrice(value: number, currency: Currency = "AZN"): string {
  const rounded = Math.round(value);
  const grouped = rounded
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, AZN_GROUP_SEPARATOR);
  return `${grouped} ${currencySymbol(currency)}`;
}

export function formatPriceShort(value: number): string {
  if (value >= 1_000_000) {
    const m = value / 1_000_000;
    return `${trimTrailingZero(m.toFixed(1))}M`;
  }
  if (value >= 1_000) {
    const k = value / 1_000;
    return `${trimTrailingZero(k.toFixed(1))}K`;
  }
  return `${value}`;
}

function trimTrailingZero(s: string): string {
  return s.replace(/\.0$/, "");
}

export function currencySymbol(currency: Currency): string {
  switch (currency) {
    case "AZN":
      return "₼";
    case "USD":
      return "$";
    case "EUR":
      return "€";
  }
}

export function formatPricePerSqm(
  value: number,
  currency: Currency = "AZN"
): string {
  return `${formatPrice(value, currency)} / m²`;
}

export function formatPriceWithPeriod(
  value: number,
  dealType: DealType,
  currency: Currency = "AZN",
  locale: "az" | "en" | "ru" = "az"
): string {
  switch (dealType) {
    case "rent":
      return `${formatPrice(value, currency)} / ${locale === "en" ? "month" : locale === "ru" ? "мес." : "ay"}`;
    case "daily":
      return `${formatPrice(value, currency)} / ${locale === "en" ? "day" : locale === "ru" ? "день" : "gün"}`;
    default:
      return formatPrice(value, currency);
  }
}

const MONTHS_AZ = [
  "yanvar",
  "fevral",
  "mart",
  "aprel",
  "may",
  "iyun",
  "iyul",
  "avqust",
  "sentyabr",
  "oktyabr",
  "noyabr",
  "dekabr"
];

export function formatDate(value: string | Date): string {
  const d = typeof value === "string" ? new Date(value) : value;
  return `${d.getDate()} ${MONTHS_AZ[d.getMonth()]}, ${d.getFullYear()}`;
}

export function timeAgo(value: string | Date, now = new Date(), locale: "az" | "en" | "ru" = "az"): string {
  const d = typeof value === "string" ? new Date(value) : value;
  const diffMs = now.getTime() - d.getTime();
  const minutes = Math.floor(diffMs / 60_000);
  if (locale !== "az") {
    const formatter = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
    if (minutes < 60) return formatter.format(-Math.max(0, minutes), "minute");
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return formatter.format(-hours, "hour");
    const days = Math.floor(hours / 24);
    if (days < 30) return formatter.format(-days, "day");
    return new Intl.DateTimeFormat(locale, { day: "numeric", month: "long", year: "numeric" }).format(d);
  }
  if (minutes < 1) return "İndicə";
  if (minutes < 60) return `${minutes} dəq əvvəl`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} saat əvvəl`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} gün əvvəl`;
  if (days < 30) return `${Math.floor(days / 7)} həftə əvvəl`;
  return formatDate(d);
}

export function areaLabel(area: number): string {
  return `${area} m²`;
}

export function formatPhoneDisplay(phone: string): string {
  return phone.replace(/(\+994)(\d{2})(\d{3})(\d{2})(\d{2})/, "+994 $2 $3 $4 $5");
}
