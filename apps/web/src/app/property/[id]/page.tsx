import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronRight } from "lucide-react";
import {
  BUILDING_TYPE_LABELS,
  FEATURE_LABELS,
  PROPERTY_TYPE_LABELS,
  REPAIR_LABELS,
  type Property
} from "@yenimenzil/types";
import { fetchPropertyById, fetchSimilarProperties } from "@/services/property-api";
import { propertyMetadata, jsonLdProperty } from "@/lib/seo";
import { formatPricePerSqm, formatPriceWithPeriod, formatDate, timeAgo } from "@/lib/format";
import { PropertyGallery } from "@/features/properties/property-gallery";
import { ContactCard } from "@/features/properties/contact-card";
import { MobileContactBar } from "@/features/properties/mobile-contact-bar";
import { ShareBar } from "@/features/properties/share-bar";
import { MortgageCalculator } from "@/features/properties/mortgage-calculator";
import { PriceAnalysisCard } from "@/features/properties/price-analysis-card";
import { PriceHistoryCard } from "@/features/properties/price-history-card";
import { AreaIntelligence } from "@/features/properties/area-intelligence";
import { PropertyBadge } from "@/features/properties/property-badge";
import { PropertyGrid } from "@/features/properties/property-grid";
import { RecentlyViewedSection } from "@/features/properties/recently-viewed";
import { PropertyViewTracker } from "@/features/properties/property-view-tracker";

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  const property = await fetchPropertyById(id);
  if (!property) return { title: "Elan tapılmadı" };
  const base = propertyMetadata(property);
  if (property.status !== "active") {
    base.robots = { index: false, follow: false };
  }
  return base;
}

function AttributeRow({
  label,
  value
}: {
  label: string;
  value?: string | number;
}) {
  if (value === undefined || value === null || value === "") return null;
  return (
    <div className="flex items-center justify-between gap-4 py-2.5 text-sm">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right font-medium text-foreground">{value}</dd>
    </div>
  );
}

function PropertySummary({ property }: { property: Property }) {
  const priceDropped =
    property.priceHistory.length >= 2 &&
    property.priceHistory.at(-1)!.price < property.priceHistory[0]!.price;

  return (
    <div className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70 md:p-6">
      <div className="flex flex-wrap items-center gap-2">
        {property.isPremium ? <PropertyBadge kind="premium" /> : null}
        {property.isPromoted ? <PropertyBadge kind="promoted" /> : null}
        {priceDropped ? <PropertyBadge kind="price_drop" /> : null}
        {property.badges.includes("new") ? <PropertyBadge kind="new" /> : null}
        {property.isVerified ? <PropertyBadge kind="verified" /> : null}
      </div>

      <div className="mt-3 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="text-[28px] font-semibold tabular-nums tracking-tight text-foreground md:text-[32px]">
          {formatPriceWithPeriod(property.price, property.dealType)}
        </span>
        {property.pricePerSqm ? (
          <span className="text-sm text-muted-foreground">
            {formatPricePerSqm(property.pricePerSqm)}
          </span>
        ) : null}
      </div>

      <h1 className="mt-2 text-[20px] font-semibold leading-snug tracking-tight text-foreground md:text-[22px]">
        {property.title}
      </h1>
      <p className="mt-1 text-[13.5px] text-muted-foreground">
        {property.location.addressText}
      </p>
      <p className="mt-2 text-[13px] tabular-nums text-muted-foreground">
        Elan nömrəsi {property.referenceCode} ·{" "}
        {timeAgo(property.publishedAt)} elan edilib ·{" "}
        {formatDate(property.publishedAt)}
      </p>

      <div className="mt-3">
        <ShareBar property={property} />
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-x-6 divide-y divide-border/70 border-t border-border/70 md:grid-cols-3">
        {property.rooms > 0 ? (
          <AttributeRow label="Otaqlar" value={property.rooms} />
        ) : null}
        {property.bedrooms ? (
          <AttributeRow label="Yataq otağı" value={property.bedrooms} />
        ) : null}
        {property.bathrooms ? (
          <AttributeRow label="Sanitar qovşağı" value={property.bathrooms} />
        ) : null}
        <AttributeRow label="Ümumi sahə" value={`${property.areaTotal} m²`} />
        {property.areaLiving ? (
          <AttributeRow label="Yaşayış sahəsi" value={`${property.areaLiving} m²`} />
        ) : null}
        {property.areaLand ? (
          <AttributeRow label="Torpaq sahəsi" value={`${property.areaLand} m²`} />
        ) : null}
        {property.floor != null && property.floor > 0 ? (
          <AttributeRow
            label="Mərtəbə"
            value={`${property.floor} / ${property.totalFloors}`}
          />
        ) : null}
        {property.buildingType ? (
          <AttributeRow
            label="Tikili növü"
            value={BUILDING_TYPE_LABELS[property.buildingType]}
          />
        ) : null}
        {property.repairStatus ? (
          <AttributeRow
            label="Təmir"
            value={REPAIR_LABELS[property.repairStatus]}
          />
        ) : null}
        {property.constructionYear ? (
          <AttributeRow label="Tikilmə ili" value={property.constructionYear} />
        ) : null}
        {property.documentType ? (
          <AttributeRow
            label="Sənədlər"
            value={
              property.documentType === "extract"
                ? "Çıxarış"
                : property.documentType === "certificate"
                  ? "Vəsiqə"
                  : "Mülkiyyət hüququ"
            }
          />
        ) : null}
        {property.mortgageAvailable ? (
          <AttributeRow label="İpoteka" value="Mümkündür" />
        ) : null}
      </dl>
    </div>
  );
}

function DescriptionSection({ property }: { property: Property }) {
  const paragraphs = property.description
    .split("\n\n")
    .map((p) => p.trim())
    .filter(Boolean);

  return (
    <section
      aria-labelledby="description-title"
      className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70 md:p-6"
    >
      <h2 id="description-title" className="text-base font-semibold text-foreground">
        Haqqında
      </h2>
      <div className="mt-3 space-y-3">
        {paragraphs.map((paragraph, i) => (
          <p
            key={i}
            className="text-[14.5px] leading-relaxed text-foreground/80"
          >
            {paragraph}
          </p>
        ))}
      </div>
    </section>
  );
}

function FeaturesSection({ property }: { property: Property }) {
  if (property.features.length === 0) return null;
  return (
    <section
      aria-labelledby="features-title"
      className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70 md:p-6"
    >
      <h2 id="features-title" className="text-base font-semibold text-foreground">
        Əmlak xüsusiyyətləri
      </h2>
      <div className="mt-4 flex flex-wrap gap-2">
        {property.features.map((feature) => (
          <span
            key={feature}
            className="rounded-full border border-border bg-surface px-3.5 py-1.5 text-[13px] font-medium text-foreground/75"
          >
            {FEATURE_LABELS[feature]}
          </span>
        ))}
      </div>
    </section>
  );
}

export default async function PropertyPage({ params }: PageProps) {
  const { id } = await params;
  const property = await fetchPropertyById(id);

  if (!property) notFound();

  if (property.status !== "active") {
    return (
      <div className="mx-auto max-w-xl px-4 py-20 text-center">
        <p className="text-3xl">📋</p>
        <h1 className="mt-4 text-xl font-semibold text-foreground">
          Bu elan mövcud deyil
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Elan satılıb, ləğv edilib və ya müvəqqəti dayandırılıb.
        </p>
        <Link
          href="/search"
          className="mt-6 inline-flex h-11 items-center justify-center rounded-[10px] bg-brand px-6 text-sm font-medium text-white hover:bg-brand-hover"
        >
          Digər elanlara bax
        </Link>
      </div>
    );
  }

  const similar = await fetchSimilarProperties(property, 4);

  return (
    <div className="mx-auto max-w-[1200px] px-4 py-5 lg:px-6 lg:py-7">
      <PropertyViewTracker property={property} />

      <nav aria-label="Breadcrumb" className="mb-4">
        <ol className="flex flex-wrap items-center gap-1.5 text-[13px] text-muted-foreground">
          <li>
            <Link href="/" className="transition-colors hover:text-brand">
              Ana səhifə
            </Link>
          </li>
          <li aria-hidden="true">
            <ChevronRight className="h-3.5 w-3.5" />
          </li>
          <li>
            <Link
              href={`/search?deal=${property.dealType}`}
              className="transition-colors hover:text-brand"
            >
              {property.dealType === "sale"
                ? "Al"
                : property.dealType === "rent"
                  ? "Kirayə"
                  : "Günlük kirayə"}
            </Link>
          </li>
          <li aria-hidden="true">
            <ChevronRight className="h-3.5 w-3.5" />
          </li>
          <li>
            <Link
              href={`/search?deal=${property.dealType}&property_type=${property.propertyType}`}
              className="transition-colors hover:text-brand"
            >
              {PROPERTY_TYPE_LABELS[property.propertyType]}
            </Link>
          </li>
          <li aria-hidden="true">
            <ChevronRight className="h-3.5 w-3.5" />
          </li>
          <li aria-current="page" className="font-medium text-foreground/80">
            {property.referenceCode}
          </li>
        </ol>
      </nav>

      {jsonLdProperty(property).map((schema, i) => (
        <script
          key={i}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
        />
      ))}

      <PropertyGallery property={property} />

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="min-w-0 space-y-5">
          <PropertySummary property={property} />
          <DescriptionSection property={property} />
          <FeaturesSection property={property} />
          <PriceAnalysisCard property={property} />
          <PriceHistoryCard property={property} />
          <AreaIntelligence property={property} />
        </div>

        <aside id="contact-card" className="scroll-mt-24 lg:sticky lg:top-20 lg:h-fit">
          <ContactCard property={property} />
          {property.mortgageAvailable ? (
            <div className="mt-4">
              <MortgageCalculator property={property} />
            </div>
          ) : null}
          {property.mortgageAvailable ? (
            <div className="mt-4 rounded-2xl bg-brand-soft p-4">
              <p className="text-sm font-semibold text-brand">İpoteka mümkündür</p>
              <p className="mt-1 text-[13px] leading-relaxed text-brand/80">
                Bu elan üçün banklar vasitəsilə ipoteka krediti təşkil oluna
                bilər. Ətraflı məlumat üçün satıcı ilə əlaqə saxlayın.
              </p>
            </div>
          ) : null}
        </aside>
      </div>

      {similar.length > 0 ? (
        <section aria-labelledby="similar-title" className="mt-12">
          <h2
            id="similar-title"
            className="mb-5 text-xl font-semibold tracking-tight text-foreground md:text-2xl"
          >
            Oxşar elanlar
          </h2>
          <PropertyGrid listings={similar} columns={4} />
        </section>
      ) : null}

      <RecentlyViewedSection excludeId={property.id} />
      <MobileContactBar property={property} />
    </div>
  );
}
