import { mapTilesUrl } from "@yenimenzil/config";

/** Resolves the raster tile URL template used by the demo map provider. */
export function getTileUrlTemplate(): string {
  return mapTilesUrl;
}

/** Attribution string required by the tile provider. */
export function getAttribution(): string {
  return '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
}
