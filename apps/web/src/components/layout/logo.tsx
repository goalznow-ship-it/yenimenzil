"use client";

import Link from "next/link";
import { MapPin } from "lucide-react";
import { useI18n } from "@/components/i18n-provider";

export function Logo({ className }: { className?: string }) {
  const { t } = useI18n();
  return (
    <Link
      href="/"
      className={`group flex items-center gap-2.5 ${className ?? ""}`}
      aria-label={`YeniMenzil.az — ${t("nav.home")}`}
    >
      <span className="relative flex h-9 w-9 items-center justify-center rounded-[12px] bg-brand text-white shadow-sm shadow-brand/25 transition-shadow group-hover:shadow-brand/40">
        <MapPin className="h-[18px] w-[18px]" strokeWidth={2.25} />
        <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-background bg-accent" />
      </span>
      <span className="text-[18px] font-semibold leading-none tracking-tight text-foreground">
        Yeni<span className="text-brand">Menzil</span>
        <span className="font-medium text-foreground/50">.az</span>
      </span>
    </Link>
  );
}
