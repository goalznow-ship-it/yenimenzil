"use client";

import * as React from "react";
import {
  Map as MapLibreMap,
  NavigationControl,
  type GeoJSONSource,
  type MapLayerMouseEvent
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { DEFAULT_VIEWPORT } from "@/lib/map/types";
import type {
  MapBounds,
  MapMarkerData,
  MapViewCallbacks
} from "@/lib/map/types";
import { getAttribution, getTileUrlTemplate } from "@/lib/map/tiles";
import { cn } from "@yenimenzil/ui";

interface MapViewProps extends MapViewCallbacks {
  markers: MapMarkerData[];
  className?: string;
  center?: { lat: number; lng: number };
  zoom?: number;
  /** Renders a "search this area" overlay button once the viewport drifts. */
  showBoundsSearch?: boolean;
  initialBounds?: MapBounds;
  searchLabel?: string;
  /** External marker highlight (e.g. from card hover). */
  highlightedId?: string | null;
}

const SOURCE_ID = "listings";
const CLUSTER_LAYER = "clusters";
const CLUSTER_COUNT_LAYER = "cluster-count";
const PRICE_BG_LAYER = "price-bg";
const PRICE_TEXT_LAYER = "price-text";

function toFeatureCollection(markers: MapMarkerData[]) {
  return {
    type: "FeatureCollection" as const,
    features: markers.map((m) => ({
      type: "Feature" as const,
      properties: {
        id: m.id,
        price: m.price,
        label: m.formattedPrice
      },
      geometry: {
        type: "Point" as const,
        coordinates: [m.point.lng, m.point.lat]
      }
    }))
  };
}

function setFeatureState(
  map: MapLibreMap,
  id: string,
  state: { hover?: boolean }
) {
  try {
    map.setFeatureState({ source: SOURCE_ID, id }, state);
  } catch {
    // feature may not exist yet
  }
}

export function MapView({
  markers,
  className,
  center,
  zoom,
  showBoundsSearch,
  searchLabel = "Bu ərazidə axtar",
  highlightedId,
  initialBounds,
  onMarkerClick,
  onMarkerHover,
  onBoundsChange,
  onSearchArea
}: MapViewProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<MapLibreMap | null>(null);
  const [loaded, setLoaded] = React.useState(false);
  const [drifted, setDrifted] = React.useState(false);

  const hoveredId = React.useRef<string | null>(null);
  const boundsRef = React.useRef<MapBounds | null>(null);

  React.useEffect(() => {
    if (!containerRef.current) return;
    const map = new MapLibreMap({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: [getTileUrlTemplate()],
            tileSize: 256,
            attribution: getAttribution(),
            maxzoom: 19
          }
        },
        layers: [
          {
            id: "osm-tiles",
            type: "raster",
            source: "osm",
            paint: { "raster-saturation": -0.08, "raster-contrast": -0.05 }
          }
        ]
      },
      center: [
        center?.lng ?? DEFAULT_VIEWPORT.center.lng,
        center?.lat ?? DEFAULT_VIEWPORT.center.lat
      ],
      zoom: zoom ?? DEFAULT_VIEWPORT.zoom,
      attributionControl: { compact: true },
      maxZoom: 18
    });

    map.addControl(
      new NavigationControl({ showCompass: false }),
      "top-right"
    );

    map.on("load", () => {
      setLoaded(true);

      const initial = map.getBounds();
      boundsRef.current = initialBounds ?? {
        north: initial.getNorth(),
        south: initial.getSouth(),
        east: initial.getEast(),
        west: initial.getWest()
      };

      map.addSource(SOURCE_ID, {
        type: "geojson",
        data: toFeatureCollection(markers),
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 42,
        promoteId: "id"
      });

      map.addLayer({
        id: CLUSTER_LAYER,
        type: "circle",
        source: SOURCE_ID,
        filter: ["has", "point_count"],
        paint: {
          "circle-color": "#15543F",
          "circle-radius": [
            "step",
            ["get", "point_count"],
            22,
            25,
            26,
            100,
            32
          ],
          "circle-opacity": 0.95,
          "circle-stroke-width": [
            "case",
            ["boolean", ["feature-state", "hover"], false],
            3,
            2
          ],
          "circle-stroke-color": "#ffffff"
        }
      });

      map.addLayer({
        id: CLUSTER_COUNT_LAYER,
        type: "symbol",
        source: SOURCE_ID,
        filter: ["has", "point_count"],
        layout: {
          "text-field": ["get", "point_count_abbreviated"],
          "text-size": 12
        },
        paint: { "text-color": "#ffffff" }
      });

      map.addLayer({
        id: PRICE_BG_LAYER,
        type: "circle",
        source: SOURCE_ID,
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-color": "#ffffff",
          "circle-radius": [
            "case",
            ["==", ["get", "label"], ""],
            10,
            24
          ],
          "circle-stroke-width": [
            "case",
            ["boolean", ["feature-state", "hover"], false],
            2.5,
            1.5
          ],
          "circle-stroke-color": "#15543F",
          "circle-opacity": 0.98,
          "circle-stroke-opacity": [
            "case",
            ["boolean", ["feature-state", "hover"], false],
            1,
            0.45
          ]
        }
      });

      map.addLayer({
        id: PRICE_TEXT_LAYER,
        type: "symbol",
        source: SOURCE_ID,
        filter: [
          "all",
          ["!", ["has", "point_count"]],
          ["!=", ["get", "label"], ""]
        ],
        layout: {
          "text-field": ["get", "label"],
          "text-size": 12,
          "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"]
        },
        paint: { "text-color": "#15543F" }
      });

      map.on("mouseenter", CLUSTER_LAYER, () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", CLUSTER_LAYER, () => {
        map.getCanvas().style.cursor = "";
      });

      map.on("click", PRICE_TEXT_LAYER, (e: MapLayerMouseEvent) => {
        const feature = e.features?.[0];
        if (!feature) return;
        const marker = markers.find((m) => m.id === feature.properties?.id);
        if (marker) onMarkerClick?.(marker);
      });

      map.on("mouseenter", PRICE_TEXT_LAYER, (e) => {
        map.getCanvas().style.cursor = "pointer";
        const id = e.features?.[0]?.properties?.id as string | undefined;
        if (id && id !== hoveredId.current) {
          setFeatureState(map, id, { hover: true });
          if (hoveredId.current)
            setFeatureState(map, hoveredId.current, { hover: false });
          hoveredId.current = id;
          onMarkerHover?.(id);
        }
      });

      map.on("mouseleave", PRICE_TEXT_LAYER, () => {
        map.getCanvas().style.cursor = "";
        if (hoveredId.current) {
          setFeatureState(map, hoveredId.current, { hover: false });
          hoveredId.current = null;
          onMarkerHover?.(null);
        }
      });

      map.on("moveend", () => {
        const b = map.getBounds();
        const next: MapBounds = {
          north: b.getNorth(),
          south: b.getSouth(),
          east: b.getEast(),
          west: b.getWest()
        };
        const prev = boundsRef.current;
        boundsRef.current = next;
        onBoundsChange?.(next);
        if (showBoundsSearch && prev) {
          const drift =
            Math.abs(prev.north - next.north) + Math.abs(prev.west - next.west);
          if (drift > 0.0015) setDrifted(true);
        }
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || !loaded) return;
    const source = map.getSource(SOURCE_ID) as GeoJSONSource | undefined;
    if (source) source.setData(toFeatureCollection(markers));
  }, [markers, loaded]);

  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || !loaded || !highlightedId) return;
    setFeatureState(map, highlightedId, { hover: true });
    return () => {
      if (mapRef.current && highlightedId) {
        setFeatureState(mapRef.current, highlightedId, { hover: false });
      }
    };
  }, [highlightedId, loaded]);

  return (
    <div className={cn("relative h-full w-full overflow-hidden", className)}>
      <div ref={containerRef} className="absolute inset-0" data-testid="map" />
      {showBoundsSearch && drifted ? (
        <button
          type="button"
          onClick={() => {
            setDrifted(false);
            onSearchArea?.();
          }}
          className="absolute left-1/2 top-3 z-10 -translate-x-1/2 whitespace-nowrap rounded-full bg-brand px-4 py-2 text-sm font-medium text-white shadow-lg shadow-brand/30 transition-transform hover:scale-[1.02] active:scale-95"
        >
          {searchLabel}
        </button>
      ) : null}
    </div>
  );
}

export { isPointInBounds } from "@/lib/map/types";
