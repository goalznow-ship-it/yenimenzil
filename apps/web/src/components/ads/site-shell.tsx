"use client";

import * as React from "react";
import type { AdPlacement } from "@yenimenzil/types";
import { cn } from "@yenimenzil/ui";
import { AdSlot } from "@/components/ads/ad-slot";

interface SiteShellProps {
  children: React.ReactNode;
  leftRailPlacement?: AdPlacement;
  rightRailPlacement?: AdPlacement;
  leftRailClassName?: string;
  rightRailClassName?: string;
}

export function SiteShell({
  children,
  leftRailPlacement: _leftRailPlacement = "LEFT_RAIL",
  rightRailPlacement: _rightRailPlacement = "RIGHT_RAIL",
  leftRailClassName,
  rightRailClassName,
}: SiteShellProps) {
  // Hide rails on small screens (less than ~1680px for 300px rails + 1440px content + margins)
  const [showRails, setShowRails] = React.useState(false);

  React.useEffect(() => {
    const checkWidth = () => {
      // 300px left + 1440px content + 300px right + 48px gaps = ~2088px minimum
      // Show if viewport is wide enough
      setShowRails(window.innerWidth >= 1680);
    };
    checkWidth();
    window.addEventListener("resize", checkWidth);
    return () => window.removeEventListener("resize", checkWidth);
  }, []);

  return (
    <div className={cn("relative min-h-screen flex", showRails ? "" : "")}>
      {/* Left Rail */}
      {showRails && (
        <aside
          className={cn(
            "fixed left-0 top-0 z-10 h-dvh w-72 flex-shrink-0",
            "pointer-events-none",
            leftRailClassName
          )}
          style={{ left: "calc((100vw - 1440px) / 2 - 324px)" }}
        >
          <div className="pointer-events-auto sticky top-24 h-fit max-h-[calc(100vh-8rem)]">
            <AdSlot
              placement="LEFT_RAIL"
              className="w-full max-w-[300px] mx-auto"
            />
          </div>
        </aside>
      )}

      {/* Main Content - centered */}
      <main className={cn("flex-1 w-full max-w-[1440px] mx-auto px-4", leftRailClassName)}>
        {children}
      </main>

      {/* Right Rail */}
      {showRails && (
        <aside
          className={cn(
            "fixed right-0 top-0 z-10 h-dvh w-72 flex-shrink-0",
            "pointer-events-none",
            rightRailClassName
          )}
          style={{ right: "calc((100vw - 1440px) / 2 - 324px)" }}
        >
          <div className="pointer-events-auto sticky top-24 h-fit max-h-[calc(100vh-8rem)]">
            <AdSlot
              placement="RIGHT_RAIL"
              className="w-full max-w-[300px] mx-auto"
            />
          </div>
        </aside>
      )}
    </div>
  );
}

/** Layout wrapper for pages that don't need side rails (mobile, narrow desktop) */
export function NarrowSiteShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex-1 w-full max-w-[1440px] mx-auto px-4">
      {children}
    </main>
  );
}

/** Determine if current viewport should show side rails */
export function useSideRails(): boolean {
  const [show, setShow] = React.useState(false);
  React.useEffect(() => {
    const check = () => setShow(window.innerWidth >= 1680);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);
  return show;
}