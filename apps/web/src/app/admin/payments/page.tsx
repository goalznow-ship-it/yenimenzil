"use client";

import * as React from "react";
import { adminApi, type AdminPayment, type WebhookEventRow } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";
import { Skeleton, Badge } from "@yenimenzil/ui";
import { Wallet, Activity, TrendingUp, Clock } from "lucide-react";

const STATUS_VARIANT: Record<string, "green" | "amber" | "red" | "neutral"> = {
  paid: "green",
  pending: "amber",
  failed: "red",
  cancelled: "neutral",
  refunded: "neutral"
};

export default function AdminPaymentsPage() {
  const [summary, setSummary] = React.useState<Awaited<
    ReturnType<typeof adminApi.paymentsSummary>
  > | null>(null);
  const [payments, setPayments] = React.useState<AdminPayment[]>([]);
  const [webhooks, setWebhooks] = React.useState<WebhookEventRow[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sum, paymentsRes, webhooksRes] = await Promise.all([
        adminApi.paymentsSummary(),
        adminApi.payments(),
        adminApi.webhookEvents()
      ]);
      setSummary(sum);
      setPayments(paymentsRes);
      setWebhooks(webhooksRes);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xəta");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void Promise.resolve().then(load);
  }, [load]);

  const byStatus = summary?.by_status ?? {};
  const statCards = [
    {
      label: "Gəlir (AZN)",
      value: (summary?.revenue_azn ?? 0).toLocaleString("az-AZ"),
      icon: TrendingUp
    },
    {
      label: "Ödənilmiş",
      value: String(byStatus.paid?.count ?? 0),
      icon: Wallet
    },
    {
      label: "Gözləmədə",
      value: String(byStatus.pending?.count ?? 0),
      icon: Clock
    },
    {
      label: "Son 24 saat",
      value: String(summary?.payments_last_24h ?? 0),
      icon: Activity
    }
  ];

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8">
      <AdminPageHeader title="Ödənişlər" subtitle="Ödənişlər və webhook teslimatları." />

      {error ? (
        <p className="mt-6 rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">
          {error}
        </p>
      ) : null}

      {loading ? (
        <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-2xl" />
          ))}
        </div>
      ) : (
        <>
          <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            {statCards.map((stat) => (
              <div
                key={stat.label}
                className="rounded-2xl bg-surface p-5 ring-1 ring-border/70"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-soft text-brand">
                  <stat.icon className="h-4.5 w-4.5" />
                </div>
                <p className="mt-3 text-2xl font-semibold tabular-nums tracking-tight">
                  {stat.value}
                </p>
                <p className="mt-0.5 text-[13px] text-muted-foreground">{stat.label}</p>
              </div>
            ))}
          </div>

          <h2 className="mt-8 mb-3 text-[15px] font-semibold">Ödənişlər</h2>
          <div className="overflow-x-auto rounded-2xl bg-surface ring-1 ring-border/70">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="border-b border-border/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="p-3 font-medium">Status</th>
                  <th className="p-3 font-medium">Provider</th>
                  <th className="p-3 text-right font-medium">Məbləğ (AZN)</th>
                  <th className="p-3 font-medium">Provider ID</th>
                  <th className="p-3 text-right font-medium">Tarix</th>
                </tr>
              </thead>
              <tbody>
                {payments.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-[13px] text-muted-foreground">
                      Ödəniş yoxdur
                    </td>
                  </tr>
                ) : (
                  payments.map((payment) => (
                    <tr key={payment.id} className="border-b border-border/50 last:border-0">
                      <td className="p-3">
                        <Badge variant={STATUS_VARIANT[payment.status] ?? "neutral"}>
                          {payment.status}
                        </Badge>
                      </td>
                      <td className="p-3">{payment.provider}</td>
                      <td className="p-3 text-right tabular-nums">
                        {(payment.amount / 100).toLocaleString("az-AZ")}
                      </td>
                      <td className="max-w-[220px] truncate p-3 text-muted-foreground">
                        {payment.provider_payment_id ?? "—"}
                      </td>
                      <td className="p-3 text-right text-muted-foreground">
                        {payment.created_at
                          ? new Date(payment.created_at).toLocaleDateString("az-AZ")
                          : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <h2 className="mt-8 mb-3 text-[15px] font-semibold">Webhook teslimatları</h2>
          <div className="overflow-x-auto rounded-2xl bg-surface ring-1 ring-border/70">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="border-b border-border/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="p-3 font-medium">Status</th>
                  <th className="p-3 font-medium">Provider</th>
                  <th className="p-3 font-medium">Hadisə</th>
                  <th className="p-3 font-medium">Xəta</th>
                  <th className="p-3 text-right font-medium">Tarix</th>
                </tr>
              </thead>
              <tbody>
                {webhooks.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-[13px] text-muted-foreground">
                      Webhook yoxdur
                    </td>
                  </tr>
                ) : (
                  webhooks.map((event) => (
                    <tr key={event.id} className="border-b border-border/50 last:border-0">
                      <td className="p-3">
                        <Badge
                          variant={
                            event.status === "processed"
                              ? "green"
                              : event.status === "failed"
                                ? "red"
                                : "neutral"
                          }
                        >
                          {event.status}
                        </Badge>
                      </td>
                      <td className="p-3">{event.provider}</td>
                      <td className="p-3 text-muted-foreground">{event.event_type ?? "—"}</td>
                      <td className="max-w-[260px] truncate p-3 text-muted-foreground">
                        {event.error ?? "—"}
                      </td>
                      <td className="p-3 text-right text-muted-foreground">
                        {event.created_at
                          ? new Date(event.created_at).toLocaleString("az-AZ")
                          : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}