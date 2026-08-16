"use client";

import * as React from "react";
import { API_BASE_URL } from "@/services/api-base";
import { dashboardApi } from "@/services/dashboard-api";
import { useAuth } from "@/store/auth";

export interface RealtimeEvent {
  type: "conversation" | "message";
  conversation_id: string;
  property_id: string | null;
}

/**
 * Live conversation events via SSE with automatic reconnect (exponential
 * backoff) and a 30s polling fallback whenever the stream is not open.
 */
export function useConversationEvents(onEvent: (event: RealtimeEvent) => void) {
  const status = useAuth((s) => s.status);
  const hydrated = useAuth((s) => s.hydrated);
  const onEventRef = React.useRef(onEvent);

  const [connected, setConnected] = React.useState(false);
  const [unread, setUnread] = React.useState(0);

  React.useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  React.useEffect(() => {
    if (status !== "authenticated") {
      return;
    }

    let source: EventSource | null = null;
    let retryDelay = 1000;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let pollTimer: ReturnType<typeof setInterval> | null = null;

    const refreshUnread = async () => {
      try {
        setUnread(await dashboardApi.unreadConversationCount());
      } catch {
        /* transient */
      }
    };

    const startPolling = () => {
      if (pollTimer) clearInterval(pollTimer);
      pollTimer = setInterval(refreshUnread, 30_000);
      void refreshUnread();
    };

    const open = () => {
      source = new EventSource(`${API_BASE_URL}/conversations/stream`, {
        withCredentials: true
      });

      source.onopen = () => {
        retryDelay = 1000;
        setConnected(true);
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = null;
        void refreshUnread();
      };

      source.onmessage = (raw) => {
        try {
          const event = JSON.parse(raw.data) as RealtimeEvent;
          onEventRef.current(event);
        } catch {
          /* ignore malformed payloads */
        }
      };

      source.onerror = () => {
        source?.close();
        source = null;
        setConnected(false);
        startPolling();
        retryTimer = setTimeout(open, retryDelay);
        retryDelay = Math.min(retryDelay * 2, 30_000);
      };
    };

    open();

    return () => {
      source?.close();
      if (retryTimer) clearTimeout(retryTimer);
      if (pollTimer) clearInterval(pollTimer);
      setConnected(false);
    };
  }, [status, hydrated]);

  return { connected, unread };
}