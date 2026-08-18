import Link from "next/link";
import { MapPin } from "lucide-react";

export function Logo({ className }: { className?: string }) {
  return (
    <Link
      href="/"
      className={`group flex items-center gap-2.5 ${className ?? ""}`}
      aria-label="IdealEv.az — Ana səhifə"
    >
      <span className="relative flex h-9 w-9 items-center justify-center rounded-[12px] bg-brand text-white shadow-sm shadow-brand/25 transition-shadow group-hover:shadow-brand/40">
        <MapPin className="h-[18px] w-[18px]" strokeWidth={2.25} />
        <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-background bg-accent" />
      </span>
      <span className="text-[18px] font-semibold leading-none tracking-tight text-foreground">
        Ideal<span className="text-brand">Ev</span>
        <span className="font-medium text-foreground/50">.az</span>
      </span>
    </Link>
  );
}
