"use client";

import * as React from "react";
import type { Property } from "@yenimenzil/types";
import { track } from "@/services/analytics";
import { useRecentlyViewedStore } from "@/stores/recently-viewed-store";

export function PropertyViewTracker({ property }: { property: Property }) {
  const push = useRecentlyViewedStore((s) => s.push);

  React.useEffect(() => {
    track("PROPERTY_VIEW", {
      propertyId: property.id,
      referenceCode: property.referenceCode
    });
    push(property.id);
  }, [property.id, property.referenceCode, push]);

  return null;
}
