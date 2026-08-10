import * as React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "./cn";

interface SectionHeadingProps {
  title: string;
  subtitle?: string;
  linkHref?: string;
  linkLabel?: string;
  className?: string;
  align?: "start" | "center";
}

function SectionHeading({
  title,
  subtitle,
  linkHref,
  linkLabel = "Hamısına bax",
  className,
  align = "start"
}: SectionHeadingProps) {
  return (
    <div
      className={cn(
        "mb-5 flex items-end justify-between gap-4",
        align === "center" && "flex-col items-center text-center",
        className
      )}
    >
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-foreground sm:text-2xl">
          {title}
        </h2>
        {subtitle ? (
          <p className="mt-0.5 text-[13px] text-muted-foreground sm:text-sm">
            {subtitle}
          </p>
        ) : null}
      </div>
      {linkHref ? (
        <Link
          href={linkHref}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-brand/20 bg-brand-soft/60 px-3.5 py-1.5 text-[13px] font-semibold text-brand transition-colors hover:border-brand/40 hover:bg-brand-soft"
        >
          {linkLabel}
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      ) : null}
    </div>
  );
}

export { SectionHeading };
