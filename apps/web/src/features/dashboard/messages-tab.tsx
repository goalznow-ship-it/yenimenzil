"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { Skeleton, EmptyState } from "@yenimenzil/ui";
import { MessageSquare, Send, Archive, Trash2 } from "lucide-react";
import { dashboardApi, type Conversation, type Message } from "@/services/dashboard-api";
import { useAuth } from "@/store/auth";
import { timeAgo } from "@/lib/format";
import { useConversationEvents } from "@/hooks/use-conversation-events";

export function MessagesTab() {
  const user = useAuth((s) => s.user);
  const [conversations, setConversations] = React.useState<Conversation[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [selected, setSelected] = React.useState<string | null>(null);
  const [messages, setMessages] = React.useState<Message[] | null>(null);
  const [draft, setDraft] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const threadRef = React.useRef<HTMLDivElement>(null);
  const searchParams = useSearchParams();
  const pendingProperty = searchParams.get("property");

  const load = React.useCallback(() => {
    dashboardApi
      .conversations()
      .then((data) => {
        setConversations(data);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Xəta"));
  }, []);

  const loadThread = React.useCallback((conversationId: string) => {
    dashboardApi
      .messages(conversationId)
      .then((data) => setMessages(data))
      .catch((err) => setError(err instanceof Error ? err.message : "Xəta"));
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  const openedPropertyRef = React.useRef<string | null>(null);
  React.useEffect(() => {
    if (!pendingProperty || pendingProperty === openedPropertyRef.current) return;
    openedPropertyRef.current = pendingProperty;
    const existing = conversations?.find((c) => c.property_id === pendingProperty);
    if (existing) {
      void Promise.resolve().then(() => setSelected(existing.id));
      return;
    }
    dashboardApi
      .createConversation(pendingProperty, "Salam, elanla bağlı maraqlanıram.")
      .then((conversation) => {
        setSelected(conversation.id);
        load();
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Xəta"));
  }, [pendingProperty, conversations, load]);

  useConversationEvents((event) => {
    if (selected && event.conversation_id === selected) {
      loadThread(selected);
    } else {
      load();
    }
  });

  React.useEffect(() => {
    if (!selected) return;
    let cancelled = false;
    dashboardApi
      .messages(selected)
      .then((data) => {
        if (cancelled) return;
        setMessages(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Xəta");
      });
    return () => {
      cancelled = true;
    };
  }, [selected]);

  React.useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight;
    }
  }, [messages]);

  const send = async () => {
    if (!selected || !draft.trim()) return;
    setSending(true);
    try {
      const message = await dashboardApi.sendMessage(selected, draft.trim());
      setMessages((prev) => (prev ? [...prev, message] : [message]));
      setDraft("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setSending(false);
    }
  };

  if (!conversations && !error) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16 rounded-2xl" />
        ))}
      </div>
    );
  }

  if (error) {
    return <p className="rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">{error}</p>;
  }

  if (!conversations || conversations.length === 0) {
    return (
      <EmptyState
        icon={<MessageSquare className="h-7 w-7" />}
        title="Mesaj yoxdur"
        description="Elanlarla bağlı yazışmalar burada görünəcək."
      />
    );
  }

  const otherUser = (conversation: Conversation) =>
    user && conversation.seller_id === user.id
      ? conversation.buyer
      : conversation.seller;

  const activeConversation =
    conversations.find((c) => c.id === selected) ?? conversations[0]!;

  return (
    <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
      <div className="space-y-2">
        {conversations.map((conversation) => {
          const other = otherUser(conversation);
          const active = conversation.id === activeConversation.id;
          return (
            <button
              key={conversation.id}
              onClick={() => setSelected(conversation.id)}
              className={
                "w-full rounded-2xl p-3 text-left ring-1 transition-colors " +
                (active
                  ? "bg-brand-soft/60 ring-brand/30"
                  : "bg-surface ring-border/60 hover:ring-border")
              }
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-foreground/[0.06] text-sm font-bold text-foreground/70">
                  {other.full_name
                    .split(/\s+/)
                    .map((p) => p[0])
                    .slice(0, 2)
                    .join("")
                    .toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-semibold">{other.full_name}</p>
                    {conversation.last_message_at ? (
                      <span className="shrink-0 text-[11px] text-muted-foreground">
                        {timeAgo(conversation.last_message_at)}
                      </span>
                    ) : null}
                  </div>
                  <p className="truncate text-[13px] text-muted-foreground">
                    {conversation.last_message ?? "Yeni söhbət"}
                  </p>
                </div>
                {conversation.unread_count > 0 ? (
                  <span className="flex h-5 min-w-5 shrink-0 items-center justify-center rounded-full bg-brand px-1.5 text-[11px] font-bold text-white">
                    {conversation.unread_count}
                  </span>
                ) : null}
              </div>
              {conversation.property_title ? (
                <p className="mt-2 truncate border-t border-border/50 pt-2 text-[11.5px] text-muted-foreground">
                  {conversation.property_title}
                </p>
              ) : null}
            </button>
          );
        })}
      </div>

      <div className="flex min-h-[420px] flex-col rounded-2xl bg-surface ring-1 ring-border/70">
        <div className="flex items-center justify-between border-b border-border/70 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-foreground/[0.06] text-sm font-bold text-foreground/70">
              {otherUser(activeConversation)!.full_name
                .split(/\s+/)
                .map((p) => p[0])
                .slice(0, 2)
                .join("")
                .toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-semibold">{otherUser(activeConversation)!.full_name}</p>
              {activeConversation.property_title ? (
                <p className="text-[11.5px] text-muted-foreground">
                  {activeConversation.property_title}
                </p>
              ) : null}
            </div>
          </div>
          <div className="flex gap-1.5">
            <button
              onClick={async () => {
                try {
                  await dashboardApi.archiveConversation(activeConversation.id);
                  load();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Xəta");
                }
              }}
              aria-label="Arxivlə"
              className="rounded-lg p-2 text-foreground/50 transition-colors hover:bg-foreground/[0.05]"
            >
              <Archive className="h-4 w-4" />
            </button>
            <button
              onClick={async () => {
                if (!window.confirm("Söhbəti silmək istəyirsiniz?")) return;
                try {
                  await dashboardApi.deleteConversation(activeConversation.id);
                  setSelected(null);
                  load();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Xəta");
                }
              }}
              aria-label="Söhbəti sil"
              className="rounded-lg p-2 text-foreground/50 transition-colors hover:bg-red-500/10 hover:text-red-600"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div ref={threadRef} className="flex-1 space-y-3 overflow-y-auto p-4">
          {!messages ? (
            <div className="space-y-2">
              <Skeleton className="ml-auto h-10 w-2/3 rounded-2xl" />
              <Skeleton className="h-10 w-3/5 rounded-2xl" />
              <Skeleton className="ml-auto h-10 w-1/2 rounded-2xl" />
            </div>
          ) : messages.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">
              Mesaj yoxdur. Salamlama ilə başlayın.
            </p>
          ) : (
            messages.map((message) => {
              const mine = message.sender_id === user?.id;
              return (
                <div
                  key={message.id}
                  className={
                    "flex " + (mine ? "justify-end" : "justify-start")
                  }
                >
                  <div
                    className={
                      "max-w-[75%] rounded-2xl px-4 py-2.5 text-[13.5px] leading-relaxed " +
                      (mine
                        ? "rounded-br-md bg-brand text-white"
                        : "rounded-bl-md bg-foreground/[0.06] text-foreground")
                    }
                  >
                    <p>{message.content}</p>
                    <p
                      className={
                        "mt-1 text-[10.5px] " +
                        (mine ? "text-white/70" : "text-muted-foreground")
                      }
                    >
                      {timeAgo(message.created_at)}
                      {message.is_read && mine ? " · oxundu" : ""}
                    </p>
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="flex items-center gap-2 border-t border-border/70 p-3">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
            placeholder="Mesaj yazın…"
            className="min-w-0 flex-1 rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm outline-none transition-colors placeholder:text-foreground/35 focus:border-brand/60 focus:ring-2 focus:ring-brand/15"
          />
          <button
            onClick={send}
            disabled={sending || !draft.trim()}
            aria-label="Göndər"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand text-white transition-colors hover:bg-brand/90 disabled:opacity-40"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
