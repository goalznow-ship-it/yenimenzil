"use client";

import * as React from "react";
import { Skeleton, EmptyState, Button } from "@yenimenzil/ui";
import { BellRing, CheckCheck, Trash2 } from "lucide-react";
import { dashboardApi, type NotificationItem } from "@/services/dashboard-api";
import { timeAgo } from "@/lib/format";

const KIND_DOT: Record<string, string> = {
  promotion: "bg-[#c9a86a]",
  message: "bg-brand",
  price_drop: "bg-emerald-500",
  saved_search: "bg-violet-500",
  moderation: "bg-amber-500",
  general: "bg-foreground/40"
};

export function NotificationsTab() {
  const [items, setItems] = React.useState<NotificationItem[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busyId, setBusyId] = React.useState<string | null>(null);

  const load = React.useCallback(() => {
    dashboardApi
      .notifications()
      .then((data) => {
        setItems(data);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Xəta"));
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  const markRead = async (id: string) => {
    if (!items) return;
    setBusyId(id);
    try {
      await dashboardApi.markNotificationRead(id);
      setItems(items.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    } catch {
      // non-fatal
    } finally {
      setBusyId(null);
    }
  };

  const markAllRead = async () => {
    if (!items) return;
    try {
      await dashboardApi.markAllNotificationsRead();
      setItems(items.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    }
  };

  const remove = async (id: string) => {
    if (!items) return;
    setBusyId(id);
    try {
      await dashboardApi.deleteNotification(id);
      setItems(items.filter((n) => n.id !== id));
    } catch {
      // non-fatal
    } finally {
      setBusyId(null);
    }
  };

  if (!items && !error) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-2xl" />
        ))}
      </div>
    );
  }

  if (error) {
    return <p className="rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">{error}</p>;
  }

  if (!items || items.length === 0) {
    return (
      <EmptyState
        icon={<BellRing className="h-7 w-7" />}
        title="Bildiriş yoxdur"
        description="Yeni bildirişlər burada görünəcək."
      />
    );
  }

  const unreadCount = items.filter((n) => !n.is_read).length;

  return (
    <div className="space-y-3">
      {unreadCount > 0 ? (
        <div className="flex items-center justify-between">
          <p className="text-[13px] text-muted-foreground">
            {unreadCount} oxunmamış bildiriş
          </p>
          <Button variant="secondary" onClick={markAllRead} className="gap-2 text-[13px]">
            <CheckCheck className="h-4 w-4" />
            Hamısını oxunmuş işarələ
          </Button>
        </div>
      ) : null}
      {items.map((notification) => (
        <div
          key={notification.id}
          className={
            "flex gap-3 rounded-2xl p-4 ring-1 transition-colors " +
            (notification.is_read
              ? "bg-surface ring-border/60"
              : "bg-brand-soft/50 ring-brand/20")
          }
        >
          <span
            className={"mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full " + (KIND_DOT[notification.kind] ?? KIND_DOT.general)}
          />
          <button
            className="min-w-0 flex-1 text-left"
            onClick={() => {
              if (!notification.is_read) markRead(notification.id);
              if (notification.link) window.location.href = notification.link;
            }}
          >
            <div className="flex items-center justify-between gap-2">
              <p className="font-semibold text-foreground">{notification.title}</p>
              <span className="shrink-0 text-xs text-muted-foreground">
                {timeAgo(notification.created_at)}
              </span>
            </div>
            <p className="mt-0.5 text-[13px] leading-relaxed text-foreground/70">
              {notification.message}
            </p>
          </button>
          <button
            onClick={() => remove(notification.id)}
            disabled={busyId === notification.id}
            aria-label="Bildirişi sil"
            className="shrink-0 self-start rounded-lg bg-foreground/[0.04] p-1.5 text-foreground/50 transition-colors hover:bg-red-500/10 hover:text-red-600 disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
