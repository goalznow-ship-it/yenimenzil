import type { Metadata } from "next";
import { Suspense } from "react";
import { MapExplorer } from "@/features/map/map-explorer";

export const metadata: Metadata = {
  title: "Xəritədə axtar",
  description:
    "Azərbaycan üzrə daşınmaz əmlak elanlarını xəritədə kəşf et."
};

export default function MapPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-[calc(100dvh-4rem)] items-center justify-center bg-background">
          <div className="h-64 w-2/3 max-w-xl animate-pulse rounded-3xl bg-foreground/[0.05]" />
        </div>
      }
    >
      <MapExplorer />
    </Suspense>
  );
}
