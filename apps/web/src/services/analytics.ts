/**
 * Analytics event tracking stub.
 *
 * Phase 1: events are collected locally (dev console + localStorage buffer).
 * Phase 2: these calls will POST to /api/v1/analytics/events.
 * No personal information is collected.
 */

export type AnalyticsEvent =
  | "SEARCH"
  | "PROPERTY_VIEW"
  | "PROPERTY_FAVORITE"
  | "PHONE_REVEAL"
  | "WHATSAPP_CLICK"
  | "MESSAGE_CLICK"
  | "MAP_MARKER_CLICK"
  | "FILTER_APPLIED"
  | "SHARE"
  | "COMPARE";

const BUFFER_KEY = "ym-analytics-buffer";

function bufferEvents() {
  try {
    const raw = localStorage.getItem(BUFFER_KEY);
    return raw ? (JSON.parse(raw) as unknown[]) : [];
  } catch {
    return [];
  }
}

export function track(event: AnalyticsEvent, payload?: Record<string, unknown>) {
  const entry = {
    event,
    ts: new Date().toISOString(),
    ...payload
  };
  try {
    const next = [...bufferEvents(), entry].slice(-200);
    localStorage.setItem(BUFFER_KEY, JSON.stringify(next));
  } catch {
    // storage unavailable — ignore
  }
  if (process.env.NODE_ENV !== "production") {
    console.debug("[analytics]", entry);
  }
}
