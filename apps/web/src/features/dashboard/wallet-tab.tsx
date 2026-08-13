"use client";

import * as React from "react";
import { Skeleton, EmptyState, Button, Input, Badge } from "@yenimenzil/ui";
import { Wallet, Plus, Star, CreditCard } from "lucide-react";
import {
  dashboardApi,
  type Wallet as WalletData,
  type WalletTransaction,
  type PromotionCatalogItem
} from "@/services/dashboard-api";
import { formatPrice, formatDate } from "@/lib/format";

const TXN_TYPE_LABELS: Record<string, string> = {
  top_up: "Balans artımı",
  promotion: "Promosyon",
  refund: "Geri qaytarma",
  withdraw: "Çıxarış"
};

const TXN_STATUS_BADGE: Record<string, React.ComponentProps<typeof Badge>["variant"]> = {
  completed: "green",
  pending: "amber",
  failed: "red",
  cancelled: "neutral"
};

export function WalletTab() {
  const [wallet, setWallet] = React.useState<WalletData | null>(null);
  const [transactions, setTransactions] = React.useState<WalletTransaction[] | null>(null);
  const [catalog, setCatalog] = React.useState<PromotionCatalogItem[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);
  const [amount, setAmount] = React.useState("");
  const [topUpBusy, setTopUpBusy] = React.useState(false);

  React.useEffect(() => {
    dashboardApi
      .wallet()
      .then(setWallet)
      .catch((err) => setError(err instanceof Error ? err.message : "Xəta"));
    dashboardApi
      .walletTransactions()
      .then(setTransactions)
      .catch(() => undefined);
    dashboardApi
      .promotionCatalog()
      .then(setCatalog)
      .catch(() => undefined);
  }, []);

  const topUp = async () => {
    const value = Number(amount);
    if (!Number.isFinite(value) || value < 100) {
      setError("Minimal məbləğ 100 AZN-dir");
      return;
    }
    setTopUpBusy(true);
    setError(null);
    setInfo(null);
    try {
      const result = await dashboardApi.topUp(value);
      setInfo(result.detail);
      setAmount("");
      const refreshed = await dashboardApi.wallet();
      setWallet(refreshed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setTopUpBusy(false);
    }
  };

  if (!wallet) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-44 rounded-2xl" />
        <Skeleton className="h-44 rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error ? (
        <p className="rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">{error}</p>
      ) : null}
      {info ? (
        <p className="rounded-xl bg-emerald-500/10 px-3.5 py-2.5 text-[13px] text-emerald-700">
          {info}
        </p>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl bg-brand p-6 text-white shadow-sm shadow-brand/25">
          <div className="flex items-center gap-2 text-white/80">
            <Wallet className="h-5 w-5" />
            <p className="text-sm font-medium">Cari balans</p>
          </div>
          <p className="mt-3 text-4xl font-semibold tabular-nums tracking-tight">
            {formatPrice(wallet.balance)}
          </p>
          <div className="mt-5 flex gap-2">
            <Input
              type="number"
              min={100}
              placeholder="Məbləğ (AZN)"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="flex-1 border-white/20 bg-white/10 text-white placeholder:text-white/50"
            />
            <Button
              onClick={topUp}
              disabled={topUpBusy}
              className="bg-white text-brand hover:bg-white/90"
            >
              <Plus className="h-4 w-4" />
              {topUpBusy ? "Göndərilir…" : "Artır"}
            </Button>
          </div>
        </div>

        <div className="rounded-2xl bg-surface p-6 ring-1 ring-border/70">
          <div className="flex items-center gap-2">
            <Star className="h-5 w-5 text-[#c9a86a]" />
            <p className="text-sm font-semibold">Promosyon paketləri</p>
          </div>
          <p className="mt-1.5 text-[13px] leading-relaxed text-muted-foreground">
            Elanlarınızı irəli çəkin və daha çox alıcıya çatın. Balansdan avtomatik
            silinir.
          </p>
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {catalog.length === 0 ? (
              <p className="text-[13px] text-muted-foreground">
                Paketlər yüklənir…
              </p>
            ) : (
              catalog.map((item) => (
                <div
                  key={item.tier}
                  className="rounded-xl border border-border/70 px-3.5 py-3"
                >
                  <p className="text-sm font-semibold">{item.label}</p>
                  <p className="text-[11.5px] text-muted-foreground">{item.description}</p>
                  <p className="mt-1 text-[13px] font-medium tabular-nums">
                    {formatPrice(item.price)} · {item.days} gün
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-[15px] font-semibold">Əməliyyat tarixçəsi</h2>
        {!transactions ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-14 rounded-xl" />
            ))}
          </div>
        ) : transactions.length === 0 ? (
          <EmptyState
            icon={<CreditCard className="h-6 w-6" />}
            title="Əməliyyat yoxdur"
            description="Balans əməliyyatlarınız burada görünəcək."
          />
        ) : (
          <div className="divide-y divide-border/60 overflow-hidden rounded-2xl bg-surface ring-1 ring-border/70">
            {transactions.map((txn) => (
              <div key={txn.id} className="flex items-center justify-between gap-3 px-4 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium">
                    {TXN_TYPE_LABELS[txn.type] ?? txn.type}
                    {txn.reference_type === "property_promotion" ? " · elan" : ""}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(txn.created_at)}
                    {txn.note ? ` · ${txn.note}` : ""}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2.5">
                  <Badge variant={TXN_STATUS_BADGE[txn.status] ?? "neutral"}>
                    {txn.status}
                  </Badge>
                  <span
                    className={
                      "text-sm font-semibold tabular-nums " +
                      (txn.amount >= 0 ? "text-emerald-600" : "text-red-600")
                    }
                  >
                    {txn.amount >= 0 ? "+" : ""}
                    {formatPrice(txn.amount)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
