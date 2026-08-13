"use client";

import * as React from "react";
import { Link2, Check } from "lucide-react";

function XIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

function FacebookIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
    </svg>
  );
}
import type { Property } from "@yenimenzil/types";
import { siteUrl } from "@yenimenzil/config";

export function ShareBar({ property }: { property: Property }) {
  const [copied, setCopied] = React.useState(false);
  const url = `${siteUrl}/property/${property.id}`;
  const text = encodeURIComponent(`${property.title} — YeniMenzil.az`);
  const encodedUrl = encodeURIComponent(url);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable
    }
  };

  return (
    <div className="flex items-center gap-1.5">
      <button
        type="button"
        onClick={copy}
        aria-label="Linki kopyala"
        title="Linki kopyala"
        className="flex h-9 w-9 items-center justify-center rounded-xl bg-foreground/[0.05] text-foreground/60 transition-colors hover:bg-foreground/[0.09] hover:text-foreground"
      >
        {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Link2 className="h-4 w-4" />}
      </button>
      <a
        href={`https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Facebook-da paylaş"
        title="Facebook-da paylaş"
        className="flex h-9 w-9 items-center justify-center rounded-xl bg-foreground/[0.05] text-foreground/60 transition-colors hover:bg-[#1877F2]/10 hover:text-[#1877F2]"
      >
        <FacebookIcon className="h-4 w-4" />
      </a>
      <a
        href={`https://twitter.com/intent/tweet?url=${encodedUrl}&text=${text}`}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="X-də paylaş"
        title="X-də paylaş"
        className="flex h-9 w-9 items-center justify-center rounded-xl bg-foreground/[0.05] text-foreground/60 transition-colors hover:bg-foreground/[0.09] hover:text-foreground"
      >
        <XIcon className="h-3.5 w-3.5" />
      </a>
    </div>
  );
}
