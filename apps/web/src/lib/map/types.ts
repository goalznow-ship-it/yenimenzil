import type { GeoPoint } from "@yenimenzil/types";

/**
 * Map abstraction layer.
 *
 * All map provider specifics live behind this interface so the rendering
 * provider (currently MapLibre GL) can be swapped without touching business
 * code. Business code only deals with GeoPoint and MapMarkerData.
 */

export interface MapViewport {
  center: GeoPoint;
  zoom: number;
}

export interface MapMarkerData {
  id: string;
  point: GeoPoint;
  price: number;
  formattedPrice: string;
  image?: string;
  title?: string;
  address?: string;
}

export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface MapViewCallbacks {
  onMapClick?: (point: GeoPoint) => void;
  onMarkerClick?: (marker: MapMarkerData) => void;
  onMarkerHover?: (markerId: string | null) => void;
  onBoundsChange?: (bounds: MapBounds) => void;
  /** User confirmed "search this area" after panning. */
  onSearchArea?: () => void;
}

export function isPointInBounds(
  point: GeoPoint,
  bounds: MapBounds
): boolean {
  return (
    point.lat <= bounds.north &&
    point.lat >= bounds.south &&
    point.lng <= bounds.east &&
    point.lng >= bounds.west
  );
}

export const DEFAULT_VIEWPORT: MapViewport = {
  center: { lat: 40.4093, lng: 49.8671 },
  zoom: 11
};
