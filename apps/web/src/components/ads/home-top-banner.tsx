"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { AdSlot } from "./ad-slot";

export function HomeTopBanner() {
  const pathname = usePathname();

  if (pathname !== "/") return null;

  return (
    <div className="w-full border-b border-border/50 bg-background/50">
      <div className="mx-auto flex h-[100px] max-w-[1240px] items-center justify-center px-4">
        <AdSlot
          placement="HOME_TOP_BANNER"
          className="w-full max-w-[1180px] h-[90px]"
        />
      </div>
    </div>
  );
}