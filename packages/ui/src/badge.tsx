import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "./cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium leading-5",
  {
    variants: {
      variant: {
        neutral: "bg-foreground/[0.06] text-foreground",
        brand: "bg-brand-soft text-brand",
        gold: "bg-[#F5EBD8] text-[#8a6a2f]",
        green: "bg-emerald-100 text-emerald-800",
        red: "bg-red-100 text-red-700",
        amber: "bg-amber-100 text-amber-800",
        outline: "border border-border text-foreground/70",
        solid: "bg-foreground text-background"
      }
    },
    defaultVariants: {
      variant: "neutral"
    }
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
