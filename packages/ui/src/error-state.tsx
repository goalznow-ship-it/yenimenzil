import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "./cn";

const errorVariants = cva(
  "flex items-center justify-center rounded-3xl border bg-surface text-center",
  {
    variants: {
      variant: {
        default: "border-dashed border-border",
        destructive: "border-red-200 bg-red-50/40"
      },
      size: {
        sm: "px-6 py-10",
        default: "px-6 py-16"
      }
    },
    defaultVariants: { variant: "default", size: "default" }
  }
);

interface ErrorStateProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof errorVariants> {
  title: string;
  description?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}

function ErrorState({
  className,
  variant,
  size,
  title,
  description,
  action,
  icon,
  ...props
}: ErrorStateProps) {
  return (
    <div
      className={cn(errorVariants({ variant, size }), className)}
      {...props}
    >
      <div>
        {icon ? <div className="flex justify-center">{icon}</div> : null}
        <h3 className="text-base font-semibold text-foreground">{title}</h3>
        {description ? (
          <p className="mx-auto mt-1.5 max-w-md text-sm text-muted-foreground">
            {description}
          </p>
        ) : null}
        {action ? <div className="mt-5">{action}</div> : null}
      </div>
    </div>
  );
}

export { ErrorState };
