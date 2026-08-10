"use client";

import * as React from "react";
import type { Property } from "@yenimenzil/types";
import { track } from "@/services/analytics";

export function PropertyViewTracker({ property }: { property: Property }) {
  React.useEffect(() => {
    track("PROPERTY_VIEW", {
      propertyId: property.id,
      referenceCode: property.referenceCode
    });
  }, [property.id, property.referenceCode]);

  return null;
}
