/**
 * Dashboard API client — wraps the user-facing endpoints used by the
 * /profile dashboard: my listings, saved searches, notifications,
 * conversations/messages, wallet + promotions, and the summary endpoint.
 * Auth is via httpOnly cookies (same as auth-api).
 */

import { API_BASE_URL } from "@/services/api-base";

const BASE = API_BASE_URL;

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init.headers },
    ...init
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      (body && typeof body.detail === "string" && body.detail) ||
      (body && Array.isArray(body.detail)
        ? body.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ")
        : null) ||
      "Xəta baş verdi";
    throw new ApiError(response.status, detail);
  }
  return body as T;
}

export interface DashboardSummary {
  property_status_counts: Record<string, number>;
  total_views: number;
  total_favorites: number;
  unread_notifications: number;
}

export interface SavedSearch {
  id: string;
  user_id: string;
  name: string;
  filters: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SavedSearchInput {
  name: string;
  filters: Record<string, unknown>;
  is_active?: boolean;
}

export interface NotificationItem {
  id: string;
  user_id: string;
  title: string;
  message: string;
  is_read: boolean;
  kind: string;
  link: string | null;
  created_at: string;
}

export interface NotificationPreference {
  email_notifications: boolean;
  push_notifications: boolean;
  digest_frequency: string;
  [key: string]: unknown;
}

export interface MessageUser {
  id: string;
  full_name: string;
  avatar_url: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

export interface Conversation {
  id: string;
  property_id: string | null;
  buyer_id: string;
  seller_id: string;
  last_message_at: string | null;
  buyer_archived: boolean;
  seller_archived: boolean;
  buyer_blocked: boolean;
  seller_blocked: boolean;
  created_at: string;
  buyer: MessageUser;
  seller: MessageUser;
  property_title: string | null;
  property_cover: string | null;
  unread_count: number;
  last_message: string | null;
}

export interface Wallet {
  id: string;
  user_id: string;
  balance: number;
  created_at: string;
}

export interface WalletTransaction {
  id: string;
  amount: number;
  type: string;
  status: string;
  reason: string | null;
  reference_type: string | null;
  reference_id: string | null;
  note: string | null;
  created_at: string;
}

export interface PromotionCatalogItem {
  tier: string;
  label: string;
  price: number;
  days: number;
  description: string;
}

export interface Payment {
  id: string;
  amount: number;
  currency: string;
  status: string;
  provider: string;
  provider_payment_id: string | null;
  checkout_url: string | null;
  failure_reason: string | null;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface TopUpResult {
  payment: Payment;
  detail: string;
}

export interface PromotionPurchaseResult {
  transaction: WalletTransaction;
  promotion_status: string;
  expires_at: string | null;
  detail: string;
}

export interface MyPropertySummary {
  id: string;
  title: string;
  price: number;
  currency: string;
  deal_type: string;
  property_type: string;
  status: string;
  views: number;
  is_promoted: boolean;
  published_at: string | null;
  location_city: string | null;
  location_district: string | null;
  cover_image: string | null;
}

export interface PropertyRead {
  id: string;
  reference_code: string;
  slug: string;
  title: string;
  price: number;
  currency: string;
  status: string;
  is_promoted: boolean;
  is_premium: boolean;
  promotion_expires_at: string | null;
  published_at: string | null;
  expires_at: string | null;
  cover_image: string | null;
  image_count: number;
  description: string;
}

export const dashboardApi = {
  async summary(): Promise<DashboardSummary> {
    return request("/users/me/dashboard");
  },

  async myProperties(): Promise<MyPropertySummary[]> {
    return request("/properties/mine");
  },

  async deleteProperty(id: string): Promise<void> {
    return request(`/properties/${id}`, { method: "DELETE" });
  },

  async duplicateProperty(id: string): Promise<PropertyRead> {
    return request(`/properties/${id}/duplicate`, { method: "POST" });
  },

  async renewProperty(id: string): Promise<PropertyRead> {
    return request(`/properties/${id}/renew`, { method: "POST" });
  },

  async deactivateProperty(id: string): Promise<PropertyRead> {
    return request(`/properties/${id}/deactivate`, { method: "POST" });
  },

  async reactivateProperty(id: string): Promise<PropertyRead> {
    return request(`/properties/${id}/reactivate`, { method: "POST" });
  },

  async listingAnalytics(id: string): Promise<{
    property_id: string;
    views: number;
    favorites: number;
    phone_reveals: number;
    whatsapp_clicks: number;
    messages: number;
    viewing_requests: number;
  }> {
    return request(`/properties/${id}/analytics`);
  },

  async listSavedSearches(): Promise<SavedSearch[]> {
    return request("/saved-searches");
  },

  async createSavedSearch(input: SavedSearchInput): Promise<SavedSearch> {
    return request("/saved-searches", {
      method: "POST",
      body: JSON.stringify(input)
    });
  },

  async updateSavedSearch(id: string, patch: Partial<SavedSearchInput>): Promise<SavedSearch> {
    return request(`/saved-searches/${id}`, {
      method: "PATCH",
      body: JSON.stringify(patch)
    });
  },

  async deleteSavedSearch(id: string): Promise<void> {
    return request(`/saved-searches/${id}`, { method: "DELETE" });
  },

  async notifications(limit = 100): Promise<NotificationItem[]> {
    return request(`/notifications?limit=${limit}`);
  },

  async unreadNotificationCount(): Promise<number> {
    const { unread } = await request<{ unread: number }>("/notifications/unread-count");
    return unread;
  },

  async markNotificationRead(id: string): Promise<NotificationItem> {
    return request(`/notifications/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_read: true })
    });
  },

  async markAllNotificationsRead(): Promise<void> {
    return request("/notifications/mark-all-read", { method: "POST" });
  },

  async deleteNotification(id: string): Promise<void> {
    return request(`/notifications/${id}`, { method: "DELETE" });
  },

  async notificationPreferences(): Promise<NotificationPreference> {
    return request("/notifications/preferences");
  },

  async updateNotificationPreferences(
    prefs: Partial<NotificationPreference>
  ): Promise<NotificationPreference> {
    return request("/notifications/preferences", {
      method: "PUT",
      body: JSON.stringify(prefs)
    });
  },

  async conversations(): Promise<Conversation[]> {
    return request("/conversations");
  },

  async unreadConversationCount(): Promise<number> {
    const { total } = await request<{ total: number; conversations: number }>(
      "/conversations/unread-count"
    );
    return total;
  },

  async messages(conversationId: string): Promise<Message[]> {
    return request(`/conversations/${conversationId}/messages`);
  },

  async sendMessage(conversationId: string, content: string): Promise<Message> {
    return request(`/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content })
    });
  },

  async archiveConversation(conversationId: string): Promise<void> {
    return request(`/conversations/${conversationId}/archive`, { method: "PATCH" });
  },

  async deleteConversation(conversationId: string): Promise<void> {
    return request(`/conversations/${conversationId}`, { method: "DELETE" });
  },

  async wallet(): Promise<Wallet> {
    return request("/wallet");
  },

  async walletTransactions(): Promise<WalletTransaction[]> {
    return request("/wallet/transactions");
  },

  async topUp(amount: number): Promise<TopUpResult> {
    return request("/wallet/top-up", {
      method: "POST",
      body: JSON.stringify({
        amount,
        idempotency_key: crypto.randomUUID()
      })
    });
  },

  async walletPayments(): Promise<Payment[]> {
    return request("/wallet/payments");
  },

  async cancelPayment(paymentId: string): Promise<Payment> {
    return request(`/wallet/payments/${paymentId}/cancel`, { method: "POST" });
  },

  async promotionCatalog(): Promise<PromotionCatalogItem[]> {
    return request("/wallet/promotions/catalog");
  },

  async purchasePromotion(propertyId: string, tier: string): Promise<PromotionPurchaseResult> {
    return request("/wallet/promotions", {
      method: "POST",
      body: JSON.stringify({ property_id: propertyId, tier })
    });
  }
};
