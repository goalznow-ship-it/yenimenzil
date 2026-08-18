import type { Metadata } from "next";
import type { Property } from "@yenimenzil/types";
import { siteUrl } from "@yenimenzil/config";

export function propertyMetadata(property: Property): Metadata {
  const title = property.title;
  const description = property.description.slice(0, 155);
  const url = `${siteUrl}/property/${property.id}`;
  const image = property.images[0]?.src;

  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: {
      title,
      description,
      url,
      siteName: "IdealEv.az",
      locale: "az_AZ",
      type: "website",
      images: image
        ? [{ url: image, width: 1200, height: 900, alt: title }]
        : undefined
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: image ? [image] : undefined
    },
    other: {
      "product:availability": "in stock"
    }
  };
}

export function jsonLdProperty(property: Property) {
  const realEstateListing = {
    "@context": "https://schema.org",
    "@type": "RealEstateListing",
    "@id": `${siteUrl}/property/${property.id}#listing`,
    name: property.title,
    description: property.description,
    url: `${siteUrl}/property/${property.id}`,
    image: property.images.map((i) => i.src),
    offers: {
      "@type": "Offer",
      "@id": `${siteUrl}/property/${property.id}#offer`,
      price: property.price,
      priceCurrency: property.currency,
      availability: "https://schema.org/InStock",
      priceValidUntil: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
      seller: {
        "@type": property.seller.kind === "agency" ? "Organization" : "Person",
        name: property.seller.name,
        "@id": property.seller.id ? `${siteUrl}/seller/${property.seller.id}` : undefined
      },
      priceSpecification: {
        "@type": "UnitPriceSpecification",
        price: property.price,
        priceCurrency: property.currency,
        unitCode: "MTK" // square meter
      }
    },
    address: {
      "@type": "PostalAddress",
      addressLocality: property.location.city,
      addressRegion: property.location.district,
      addressCountry: "AZ",
      streetAddress: property.location.addressText
    },
    geo: {
      "@type": "GeoCoordinates",
      latitude: property.location.point.lat,
      longitude: property.location.point.lng
    },
    numberOfRooms: property.rooms > 0 ? property.rooms : undefined,
    floorLevel: property.floor ?? undefined,
    floorSize: {
      "@type": "QuantitativeValue",
      value: property.areaTotal,
      unitCode: "MTK"
    },
    numberOfBathrooms: property.bathrooms ?? undefined,
    numberOfBedrooms: property.bedrooms ?? undefined,
    yearBuilt: property.constructionYear ?? undefined,
    petsAllowed: property.features.includes("pets_allowed" as Property["features"][number]) ?? false,
    amenities: property.features.map((f) => f),
    realEstateAgent: {
      "@type": "RealEstateAgent",
      name: property.seller.name,
      telephone: property.seller.verifiedPhone ? property.seller.name : undefined
    },
    datePosted: property.publishedAt,
    dateModified: property.publishedAt,
    status: property.status === "active" ? "https://schema.org/ActiveActionStatus" : "https://schema.org/InactiveActionStatus"
  };

  const productSchema = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: property.title,
    description: property.description,
    image: property.images.map((i) => i.src),
    url: `${siteUrl}/property/${property.id}`,
    offers: {
      "@type": "Offer",
      price: property.price,
      priceCurrency: property.currency,
      availability: "https://schema.org/InStock"
    }
  };

  const breadcrumbList = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      {
        "@type": "ListItem",
        position: 1,
        name: "Ana səhifə",
        item: `${siteUrl}/`
      },
      {
        "@type": "ListItem",
        position: 2,
        name: property.dealType === "sale" ? "Al" : property.dealType === "rent" ? "Kirayə" : "Günlük kirayə",
        item: `${siteUrl}/search?deal=${property.dealType}`
      },
      {
        "@type": "ListItem",
        position: 3,
        name: property.propertyType,
        item: `${siteUrl}/search?deal=${property.dealType}&property_type=${property.propertyType}`
      },
      {
        "@type": "ListItem",
        position: 4,
        name: property.referenceCode,
        item: `${siteUrl}/property/${property.id}`
      }
    ]
  };

  return [realEstateListing, productSchema, breadcrumbList];
}

export function searchPageJsonLd(dealType: string, totalResults: number, baseUrl: string) {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    numberOfItems: totalResults,
    itemListElement: [],
    url: `${baseUrl}/search?deal=${dealType}`,
    name: `${dealType === "sale" ? "Satış" : dealType === "rent" ? "Kirayə" : "Günlük kirayə"} elanları`,
    description: `${totalResults} aktiv elan mövcuddur.`
  };
}
