"use client";

import * as React from "react";
import { Flag, X } from "lucide-react";
import { Button } from "@yenimenzil/ui";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const REASONS = [
  ["fake", "Saxta elan"], ["scam", "Dələduzluq şübhəsi"],
  ["wrong_price", "Qiymət yanlışdır"], ["duplicate", "Təkrar elandır"],
  ["misleading", "Məlumat aldadıcıdır"], ["expired", "Əmlak artıq mövcud deyil"],
  ["other", "Digər"]
] as const;

export function ReportListing({ propertyId }: { propertyId: string }) {
  const [open, setOpen] = React.useState(false);
  const [reason, setReason] = React.useState("fake");
  const [description, setDescription] = React.useState("");
  const [message, setMessage] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);

  const submit = async () => {
    setBusy(true); setMessage(null);
    const response = await fetch(`${API}/reports`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ property_id: propertyId, reason, description: description || null }) });
    if (response.ok) { setMessage("Şikayətiniz qəbul edildi."); setDescription(""); }
    else if (response.status === 401) setMessage("Şikayət göndərmək üçün hesabınıza daxil olun.");
    else setMessage("Şikayət göndərilə bilmədi.");
    setBusy(false);
  };

  return <>
    <button type="button" onClick={() => setOpen(true)} className="inline-flex items-center gap-1.5 text-xs text-muted-foreground transition hover:text-red-600"><Flag className="h-3.5 w-3.5"/> Şikayət et</button>
    {open ? <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/45 p-4" role="dialog" aria-modal="true" aria-label="Elan haqqında şikayət">
      <div className="w-full max-w-md rounded-2xl bg-surface p-6 shadow-2xl">
        <div className="flex items-center justify-between"><h2 className="text-lg font-semibold">Elan haqqında şikayət</h2><button onClick={() => setOpen(false)} aria-label="Bağla"><X className="h-5 w-5"/></button></div>
        <label className="mt-5 block text-sm font-medium">Səbəb</label>
        <select value={reason} onChange={(event) => setReason(event.target.value)} className="mt-2 w-full rounded-xl border border-border bg-background px-3 py-2.5 text-sm">{REASONS.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select>
        <label className="mt-4 block text-sm font-medium">Əlavə məlumat</label>
        <textarea value={description} onChange={(event) => setDescription(event.target.value.slice(0,2000))} rows={4} className="mt-2 w-full rounded-xl border border-border bg-background p-3 text-sm" placeholder="Problemi qısa izah edin..."/>
        {message ? <p className="mt-3 text-sm text-brand">{message}</p> : null}
        <div className="mt-5 flex justify-end gap-2"><Button variant="outline" onClick={() => setOpen(false)}>Ləğv et</Button><Button disabled={busy} onClick={submit}>{busy ? "Göndərilir…" : "Göndər"}</Button></div>
      </div>
    </div> : null}
  </>;
}
