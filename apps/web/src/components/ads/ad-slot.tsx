"use client";

import * as React from "react";
import type { AdCampaignPublic, AdPlacement } from "@yenimenzil/types";
import { cn } from "@yenimenzil/ui";
import { ImageWithFallback } from "@/components/common/image-with-fallback";
import { recordClick, getAdSessionKey } from "@/services/ads";

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

  React.useEffect(() => {
    if (!ad || impressionFired.current || loading) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            impressionFired.current = true;
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
  }, [ad, loading, placement]);

  if (loading) {
    const isRail = placement === "LEFT_RAIL" || placement === "RIGHT_RAIL";
    return (
      <div
        ref={adRef}
        className={cn(
          "relative overflow-hidden bg-muted/30 animate-pulse",
          isRail && "h-full w-full max-w-none min-w-0",
          className
        )}
      >
        <div className={cn("w-full", isRail ? "h-full" : "aspect-video", "bg-muted/50")} />
        {isDesktopPlacement(placement) && (
          <span className="absolute top-1 right-1 text-[10px] text-muted-foreground/60">
            Reklam
          </span>
        )}
      </div>
    );
  }

  if (error || !ad) {
    if (["HOME_TOP_BANNER", "LEFT_RAIL", "RIGHT_RAIL"].includes(placement)) {
      const isTopBanner = placement === "HOME_TOP_BANNER";
      const isRail = placement === "LEFT_RAIL" || placement === "RIGHT_RAIL";
      
      if (isTopBanner) {
        return (
          <div
            ref={adRef}
            className={cn(
              "relative overflow-hidden rounded-xl bg-gradient-to-r from-brand/10 via-brand/5 to-brand/10 border border-brand/20",
              className
            )}
            style={{ width: "100%", height: "100%" }}
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center p-4 text-brand/60">
                <div className="text-[11px] font-medium uppercase tracking-wider mb-1">Reklam</div>
                <div className="text-[10px] text-muted-foreground/50">Üst Banner</div>
              </div>
            </div>
          </div>
        );
      }
      
      if (isRail) {
        return (
          <div
            ref={adRef}
            className={cn(
              "relative overflow-hidden rounded-xl bg-gradient-to-b from-brand/10 via-brand/5 to-brand/10 border border-brand/20",
              className
            )}
            style={{ 
              width: "100%",
              height: "100%",
              maxWidth: "100%",
              minWidth: 0,
            }}
          >
            <div className="absolute inset-0 flex flex-col items-center justify-center p-0">
              <div className="text-center text-brand/60">
                <div className="text-[10px] font-medium uppercase tracking-wider mb-2">Reklam</div>
                <div className="text-[9px] text-muted-foreground/50">
                  {placement === "LEFT_RAIL" ? "Sol Rail" : "Sağ Rail"}
                </div>
              </div>
            </div>
          </div>
        );
      }
    }
    return null;
  }

  const isMobile = device === "mobile";
  const isRail = placement === "LEFT_RAIL" || placement === "RIGHT_RAIL";
  const imageUrl = isMobile ? ad.mobile_creative_url ?? ad.desktop_creative_url : ad.desktop_creative_url;

  const handleClick = (_e: React.MouseEvent<HTMLAnchorElement>) => {
    recordClick(ad.id, getAdSessionKey());
  };

  return (
    <div ref={adRef} className={cn("relative", isRail && "h-full w-full max-w-none min-w-0", className)}>
      <a
        href={ad.destination_url}
        target={ad.open_in_new_tab ? "_blank" : "_self"}
        rel={ad.open_in_new_tab ? "noopener noreferrer" : undefined}
        onClick={handleClick}
        className={cn(
          "block relative overflow-hidden",
          isRail && "h-full w-full max-w-none min-w-0"
        )}
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
          <div
            className={cn(
              "w-full bg-muted/30 flex items-center justify-center",
              isRail ? "h-full" : "aspect-video"
            )}
          >
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