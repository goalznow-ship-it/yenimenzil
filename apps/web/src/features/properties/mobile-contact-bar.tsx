"use client";

import * as React from "react";
import type { Property } from "@yenimenzil/types";
import { MessageCircle, Phone } from "lucide-react";
import { formatPrice } from "@/lib/format";
import { track } from "@/services/analytics";
import { cn } from "@yenimenzil/ui";

export function MobileContactBar({ property }: { property: Property }) {
  const [revealed, setRevealed] = React.useState(false);
  const [visible, setVisible] = React.useState(false);

  React.useEffect(() => {
    const onScroll = () => {
      const contactCard = document.getElementById("contact-card");
      if (!contactCard) return;
      const rect = contactCard.getBoundingClientRect();
      setVisible(rect.top > window.innerHeight);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const scrollToContact = () => {
    document
      .getElementById("contact-card")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div
      className={cn(
        "fixed inset-x-0 bottom-0 z-40 border-t border-border/70 bg-surface/95 px-4 pb-[max(env(safe-area-inset-bottom),12px)] pt-3 shadow-[0_-4px_16px_rgba(20,23,22,0.08)] backdrop-blur transition-transform duration-300 lg:hidden",
        visible ? "translate-y-0" : "translate-y-full"
      )}
    >
      <div className="mx-auto flex max-w-xl items-center gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-bold text-foreground">
            {formatPrice(property.price, property.currency)}
          </p>
          <p className="text-[11px] text-muted-foreground">
            {property.dealType === "rent"
              ? "aylıq kirayə"
              : property.dealType === "daily"
                ? "günlük"
                : "satış"}
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            if (!revealed) {
              setRevealed(true);
              track("PHONE_REVEAL", {
                propertyId: property.id,
                sellerId: property.seller.id
              });
            } else {
              scrollToContact();
            }
          }}
          className="inline-flex h-11 flex-1 items-center justify-center gap-2 rounded-[10px] bg-brand px-3 text-sm font-semibold text-white transition-colors hover:bg-brand-hover"
        >
          <Phone className="h-4 w-4" />
          {revealed ? "Əlaqə üçün basın" : "Telefonu göstər"}
        </button>
        <button
          type="button"
          onClick={scrollToContact}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-[10px] border border-border bg-surface px-3 text-sm font-medium text-foreground/80 transition-colors hover:border-brand/40"
          aria-label="Mesaj yaz"
        >
          <MessageCircle className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}