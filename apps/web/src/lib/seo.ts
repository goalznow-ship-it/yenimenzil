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
      siteName: "YeniMenzil.az",
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
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: property.title,
    description: property.description,
    image: property.images.map((i) => i.src),
    url: `${siteUrl}/property/${property.id}`,
    offers: {
      "@type": "Offer",
      price: property.price,
      priceCurrency: property.currency
    },
    address: {
      "@type": "PostalAddress",
      addressLocality: property.location.city,
      addressRegion: property.location.district,
      addressCountry: "AZ"
    }
  };
}
