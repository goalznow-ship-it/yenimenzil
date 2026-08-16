"use client";

import * as React from "react";
import type { AdCampaignPublic, AdPlacement } from "@yenimenzil/types";
import { cn } from "@yenimenzil/ui";
import { ImageWithFallback } from "@/components/common/image-with-fallback";
import { recordImpression, recordClick, getAdSessionKey } from "@/services/ads";

interface AdSlotProps {
  placement: AdPlacement;
  className?: string;
  device?: "desktop" | "mobile";
  city?: string;
  category?: string;
  preloadedAd?: AdCampaignPublic | null;
}

export function AdSlot({
  placement,
  className,
  device = "desktop",
  city,
  category,
  preloadedAd,
}: AdSlotProps) {
  const [ad, setAd] = React.useState<AdCampaignPublic | null>(preloadedAd ?? null);
  const [loading, setLoading] = React.useState(!preloadedAd);
  const [error, setError] = React.useState<Error | null>(null);
  const adRef = React.useRef<HTMLDivElement>(null);
  const impressionFired = React.useRef(false);

  React.useEffect(() => {
    if (preloadedAd) {
      void Promise.resolve().then(() => setAd(preloadedAd));
      void Promise.resolve().then(() => setLoading(false));
      return;
    }

    let cancelled = false;
    void Promise.resolve().then(() => setLoading(true));

    import("@/services/ads")
      .then(({ fetchAdsForPlacement }) =>
        fetchAdsForPlacement(placement, { device, city, category })
      )
      .then((fetchedAd) => {
        if (!cancelled) {
          void Promise.resolve().then(() => setAd(fetchedAd));
          void Promise.resolve().then(() => setLoading(false));
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err);
          void Promise.resolve().then(() => setLoading(false));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [placement, device, city, category, preloadedAd]);

  // Fire impression when ad becomes visible (IntersectionObserver)
  React.useEffect(() => {
    if (!ad || impressionFired.current || loading) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            impressionFired.current = true;
            recordImpression(ad.id, getAdSessionKey());
            observer.disconnect();
            break;
          }
        }
      },
      { threshold: 0.5 }
    );

    if (adRef.current) {
      observer.observe(adRef.current);
    }
    return () => observer.disconnect();
  }, [ad, loading]);

  if (loading) {
    return (
      <div
        ref={adRef}
        className={cn(
          "relative overflow-hidden bg-muted/30 animate-pulse",
          className
        )}
      >
        <div className="aspect-video w-full bg-muted/50" />
        {isDesktopPlacement(placement) && (
          <span className="absolute top-1 right-1 text-[10px] text-muted-foreground/60">
            Reklam
          </span>
        )}
      </div>
    );
  }

  if (error || !ad) {
    return null; // collapse cleanly per requirements
  }

  const isMobile = device === "mobile";
  const imageUrl = isMobile ? ad.mobile_creative_url ?? ad.desktop_creative_url : ad.desktop_creative_url;

  const handleClick = (_e: React.MouseEvent<HTMLAnchorElement>) => {
    // Allow default navigation; record click asynchronously
    recordClick(ad.id, getAdSessionKey());
  };

  return (
    <div ref={adRef} className={cn("relative", className)}>
      <a
        href={ad.destination_url}
        target={ad.open_in_new_tab ? "_blank" : "_self"}
        rel={ad.open_in_new_tab ? "noopener noreferrer" : undefined}
        onClick={handleClick}
        className="block relative overflow-hidden"
      >
        {imageUrl && (
          <ImageWithFallback
            src={imageUrl}
            alt={ad.alt_text ?? ""}
            fill
            sizes="100vw"
            className="object-cover transition-opacity duration-300"
            placeholder="blur"
          />
        )}
        {!imageUrl && (
          <div className="aspect-video w-full bg-muted/30 flex items-center justify-center">
            <span className="text-sm text-muted-foreground">
              {ad.alt_text ?? "Reklam"}
            </span>
          </div>
        )}
        {isDesktopPlacement(placement) && (
          <span className="absolute top-1 right-1 text-[10px] font-medium text-white/80 bg-black/40 px-1.5 py-0.5 rounded">
            Reklam
          </span>
        )}
      </a>
    </div>
  );
}

function isDesktopPlacement(placement: AdPlacement): boolean {
  return !placement.startsWith("MOBILE_");
}