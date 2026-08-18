"use client";

import { useState, useEffect } from "react";

const PLACEMENTS = ["LEFT_RAIL", "RIGHT_RAIL", "HOME_TOP", "HOME_MIDDLE", "SEARCH_TOP", "SEARCH_INLINE", "SEARCH_BOTTOM", "PROPERTY", "MOBILE"];

interface Campaign {
  id: number;
  name: string;
  placement: string;
  destination_url: string;
  is_active: boolean;
  impressions: number;
  clicks: number;
}

export default function AdminAdvertisingPage() {
  const { campaigns, setCampaigns } = useAdvertising();

  useEffect(() => {
    fetch("/api/admin/advertising", { credentials: "include" }).then(r => r.json()).then(setCampaigns);
  }, []);

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    const target = e.target as HTMLFormElement;
    const name = (target.querySelector('input[name="name"]') as HTMLInputElement).value;
    const placement = (target.querySelector('select[name="placement"]') as HTMLSelectElement).value;
    const dest = (target.querySelector('input[name="destination_url"]') as HTMLInputElement).value;
    try {
      fetch("/api/admin/advertising", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, placement, destination_url: dest })
      });
    } catch (err) { console.error(err); }
    fetch("/api/admin/advertising", { credentials: "include" }).then(r => r.json()).then(setCampaigns);
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Reklam KampanYönetimi</h2>
      <div className="card border rounded-xl p-6 mb-6">
        <h3 className="font-semibold mb-4">Yeni Kampanya</h3>
        <form onSubmit={handleCreate}>
          <div><label>Kampa Adı</label><input name="name" required defaultValue="" /></div>
          <div><label>Plasiman</label><select name="placement" required><option value="">Seçiniz</option>{PLACEMENTS.map((p) => <option key={p} value={p}>{p}</option>)}</select></div>
          <div><label>Hedef URL</label><input name="destination_url" type="url" defaultValue="https://" /></div>
          <div><label>Öncelik</label><input name="priority" min="1" max="10" defaultValue="1" /></div>
          <button type="submit" className="w-full rounded border px-3 py-2 text-sm font-medium text-white bg-brand hover:bg-brand/90 mt-4">Kampanya Oluştur</button>
        </form>
      </div>
      <div className="card rounded-xl overflow-x-auto">
        <table className="w-full min-w-[600px] text-sm"><thead><tr className="border-b border-gray-200"><th className="px-4 py-3 text-sm font-medium text-foreground/60">Adı</th><th className="px-4 py-3 text-sm font-medium text-foreground/60">Plasiman</th><th className="px-4 py-3 text-sm font-medium text-foreground/60">Hedef URL</th><th className="px-4 py-3 text-sm font-medium text-foreground/60">Status</th><th className="px-4 py-3 text-sm font-medium text-foreground/60">Gösterim</th><th className="px-4 py-3 text-sm font-medium text-foreground/60">Tıklama</th><th className="px-4 py-3 text-sm font-medium text-foreground/60">İşlemler</th></tr></thead>
        <tbody>{campaigns.map((c) => <tr key={c.id} className="border-b"><td className="px-4 py-3">{c.name}</td><td className="px-4 py-3">{c.placement}</td><td className="px-4 py-3">{c.destination_url ? c.destination_url : "-"}</td><td className="px-4 py-3">Aktif</td><td className="px-4 py-3">{c.impressions || 0}</td><td className="px-4 py-3">{c.clicks || 0}</td><td className="px-4 py-3"><button className="rounded border px-3 py-2 text-sm">Düzenle</button></td></tr>)}</tbody></table>
      </div>
      <div>Toplam Gösterim: {campaigns.reduce((s: number, c) => s + (c.impressions || 0), 0)}</div><div>Toplam Tıklama: {campaigns.reduce((s: number, c) => s + (c.clicks || 0), 0)}</div>
    </div>
  );
}

function useAdvertising() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  useEffect(() => {
    fetch("/api/admin/advertising", { credentials: "include" }).then(r => r.json()).then(setCampaigns);
  }, []);
  return { campaigns, setCampaigns };
}