"use client";

import * as React from "react";
import { Button } from "@yenimenzil/ui";
import { Cookie } from "lucide-react";

const CONSENT_KEY = "yenimenzil-cookie-consent";

function getConsent(): boolean {
  try {
    return localStorage.getItem(CONSENT_KEY) === "accepted";
  } catch {
    return false;
  }
}

export function CookieConsent() {
  const [visible, setVisible] = React.useState(false);

  React.useEffect(() => {
    const timer = window.setTimeout(() => {
      setVisible(!getConsent());
    }, 1200);
    return () => window.clearTimeout(timer);
  }, []);

  const accept = () => {
    try {
      localStorage.setItem(CONSENT_KEY, "accepted");
    } catch {
      // storage unavailable
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      role="region"
      aria-label="Kukilər haqqında məlumat"
      className="fixed inset-x-4 bottom-4 z-50 mx-auto max-w-xl rounded-2xl bg-surface p-4 shadow-lift ring-1 ring-border/70 md:inset-x-auto md:left-4 md:right-4"
    >
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-soft text-brand">
          <Cookie className="h-4.5 w-4.5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold">Kukilərdən istifadə</p>
          <p className="mt-0.5 text-[13px] leading-relaxed text-muted-foreground">
            Saytın işləməsi və təcrübənizi yaxşılaşdırmaq üçün kukilərdən
            istifadə edirik. Davam etməklə bununla razılaşırsınız.
          </p>
          <div className="mt-3 flex gap-2">
            <Button onClick={accept} className="text-[13px]">
              Razıyam
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
