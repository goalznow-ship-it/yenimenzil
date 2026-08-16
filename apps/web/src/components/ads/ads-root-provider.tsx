"use client";

import * as React from "react";
import type { AdPlacement } from "@yenimenzil/types";
import { AdsProvider } from "@/components/ads/ads-context";

export function AdsRootProvider({
  children,
  placements = [],
  device = "desktop",
}: {
  children: React.ReactNode;
  placements?: AdPlacement[];
  device?: "desktop" | "mobile";
}) {
    return (
      <AdsProvider placements={placements ?? []} device={device}>
        {children}
      </AdsProvider>
    );
}