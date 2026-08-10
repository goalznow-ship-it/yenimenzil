"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "./cn";

type TabsVariant = NonNullable<VariantProps<typeof tabsListVariants>["variant"]>;

interface TabsContextValue {
  value: string;
  variant: TabsVariant;
  onValueChange: (value: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | null>(null);

function useTabsContext() {
  const ctx = React.useContext(TabsContext);
  if (!ctx) throw new Error("Tabs components must be used within <Tabs>");
  return ctx;
}

const tabsListVariants = cva(
  "inline-flex items-center gap-1 rounded-xl bg-foreground/[0.04] p-1 text-foreground/60",
  {
    variants: {
      variant: {
        default: "",
        underline: "rounded-none bg-transparent p-0"
      }
    },
    defaultVariants: { variant: "default" }
  }
);

const tabsTriggerVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/30 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "data-[state=active]:bg-surface data-[state=active]:text-foreground data-[state=active]:shadow-sm",
        underline:
          "relative rounded-none border-b-[2.5px] border-transparent px-1.5 pb-[9px] pt-1.5 text-[15px] font-medium text-foreground/55 transition-all hover:text-foreground data-[state=active]:border-brand data-[state=active]:font-semibold data-[state=active]:text-brand"
      }
    },
    defaultVariants: { variant: "default" }
  }
);

function Tabs({
  value,
  onValueChange,
  variant = "default",
  children,
  className
}: React.PropsWithChildren<{
  value: string;
  onValueChange: (value: string) => void;
  variant?: TabsVariant;
  className?: string;
}>) {
  return (
    <TabsContext.Provider value={{ value, variant, onValueChange }}>
      <div className={cn("w-full", className)}>{children}</div>
    </TabsContext.Provider>
  );
}

const TabsList = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
  const { variant } = useTabsContext();
  return (
    <div
      ref={ref}
      role="tablist"
      className={cn(tabsListVariants({ variant }), className)}
      {...props}
    />
  );
});
TabsList.displayName = "TabsList";

const TabsTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { value: string }
>(({ className, value, ...props }, ref) => {
  const { value: currentValue, variant, onValueChange } = useTabsContext();
  const active = currentValue === value;
  return (
    <button
      ref={ref}
      role="tab"
      aria-selected={active}
      data-state={active ? "active" : "inactive"}
      className={cn(tabsTriggerVariants({ variant }), className)}
      onClick={() => onValueChange(value)}
      {...props}
    />
  );
});
TabsTrigger.displayName = "TabsTrigger";

export { Tabs, TabsList, TabsTrigger };
