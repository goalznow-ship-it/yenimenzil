/**
 * Analytics event tracking.
 *
 * Phase 2: events are sent to the backend API and also stored locally.
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
const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/analytics/events`;

function bufferEvents() {
  try {
    const raw = localStorage.getItem(BUFFER_KEY);
    return raw ? (JSON.parse(raw) as unknown[]) : [];
  } catch {
    return [];
  }
}

export async function track(event: AnalyticsEvent, payload?: Record<string, unknown>) {
  const entry = {
    event,
    ts: new Date().toISOString(),
    ...payload
  };
  // Store locally first
  try {
    const next = [...bufferEvents(), entry].slice(-200);
    localStorage.setItem(BUFFER_KEY, JSON.stringify(next));
  } catch {
    // storage unavailable — ignore
  }

  // Send to backend
  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        event_type: event,
        payload: payload ?? {},
        // We don't have user_id, property_id, ip_address, user_agent here.
        // The backend can extract ip_address and user_agent from the request.
        // We'll leave them as null and let the backend handle it.
        // Alternatively, we could try to get the user from cookies, but it's complex.
        // For now, we'll send only event_type and payload.
        // The backend endpoint expects user_id, property_id, etc. but they are nullable.
      }),
    });
    if (!response.ok) {
      console.warn("[analytics] Failed to send event to backend", response.status, response.statusText);
    }
  } catch (err) {
    // Network error or other issue
    console.warn("[analytics] Error sending event to backend", err);
  }

  if (process.env.NODE_ENV !== "production") {
    console.debug("[analytics]", entry);
  }
}
