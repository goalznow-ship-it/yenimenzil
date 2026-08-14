"use client";

import * as React from "react";
import { Building2, Plus } from "lucide-react";
import { Button, Input } from "@yenimenzil/ui";
import { AdminPageHeader } from "../layout";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
type Developer = { id: string; name: string };
type Complex = { id: string; name: string; address: string; is_published: boolean; developer: Developer };

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, { credentials: "include", headers: { "Content-Type": "application/json" }, ...init });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail ?? "Əməliyyat uğursuz oldu");
  return body as T;
}

export default function AdminComplexesPage() {
  const [developers, setDevelopers] = React.useState<Developer[]>([]);
  const [items, setItems] = React.useState<Complex[]>([]);
  const [message, setMessage] = React.useState("");
  const [developerName, setDeveloperName] = React.useState("");
  const [form, setForm] = React.useState({ developer_id: "", name: "", slug: "", address: "", min_price: "", price_per_sqm_from: "" });
  const load = React.useCallback(async () => { try { const [devs, complexes] = await Promise.all([api<Developer[]>("/developments/developers"), api<Complex[]>("/developments/admin/complexes")]); setDevelopers(devs); setItems(complexes); setForm(v => ({ ...v, developer_id: v.developer_id || devs[0]?.id || "" })); } catch (error) { setMessage(error instanceof Error ? error.message : "Xəta"); } }, []);
  React.useEffect(() => { void load(); }, [load]);

  const slugify = (value: string) => value.toLocaleLowerCase("az").replace(/[əƏ]/g,"e").replace(/[şŞ]/g,"s").replace(/[ğĞ]/g,"g").replace(/[çÇ]/g,"c").replace(/[öÖ]/g,"o").replace(/[üÜ]/g,"u").replace(/[ıİ]/g,"i").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
  const createDeveloper = async () => { if (!developerName.trim()) return; await api("/developments/developers", { method: "POST", body: JSON.stringify({ name: developerName, slug: slugify(developerName), is_verified: true }) }); setDeveloperName(""); setMessage("Developer əlavə edildi"); await load(); };
  const createComplex = async () => { try { await api("/developments/complexes", { method: "POST", body: JSON.stringify({ ...form, min_price: form.min_price ? Number(form.min_price) : null, price_per_sqm_from: form.price_per_sqm_from ? Number(form.price_per_sqm_from) : null, is_published: true, gallery: [], amenities: [], unit_types: [] }) }); setForm(v => ({ ...v, name: "", slug: "", address: "", min_price: "", price_per_sqm_from: "" })); setMessage("Kompleks yayımlandı"); await load(); } catch (error) { setMessage(error instanceof Error ? error.message : "Xəta"); } };

  return <div><AdminPageHeader title="Yaşayış kompleksləri" subtitle="Developer və yeni tikili layihələrini idarə edin" icon={Building2}/>
    {message && <p className="mb-4 rounded-xl bg-brand-soft p-3 text-sm text-brand">{message}</p>}
    <div className="mb-6 grid gap-5 lg:grid-cols-2">
      <section className="rounded-2xl border border-border/60 bg-surface p-5"><h2 className="mb-4 font-semibold">Yeni developer</h2><div className="flex gap-2"><Input value={developerName} onChange={e=>setDeveloperName(e.target.value)} placeholder="Tikinti şirkətinin adı"/><Button onClick={createDeveloper}><Plus className="mr-1 h-4 w-4"/>Əlavə et</Button></div></section>
      <section className="rounded-2xl border border-border/60 bg-surface p-5"><h2 className="mb-4 font-semibold">Yeni kompleks</h2><div className="grid gap-3 sm:grid-cols-2"><select className="h-10 rounded-xl border border-border/60 bg-surface px-3" value={form.developer_id} onChange={e=>setForm({...form,developer_id:e.target.value})}>{developers.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select><Input placeholder="Kompleksin adı" value={form.name} onChange={e=>setForm({...form,name:e.target.value,slug:slugify(e.target.value)})}/><Input placeholder="URL adı" value={form.slug} onChange={e=>setForm({...form,slug:e.target.value})}/><Input placeholder="Ünvan" value={form.address} onChange={e=>setForm({...form,address:e.target.value})}/><Input type="number" placeholder="Başlanğıc qiymət" value={form.min_price} onChange={e=>setForm({...form,min_price:e.target.value})}/><Input type="number" placeholder="1 m²-dən" value={form.price_per_sqm_from} onChange={e=>setForm({...form,price_per_sqm_from:e.target.value})}/><Button className="sm:col-span-2" disabled={!form.developer_id || !form.name || !form.slug || !form.address} onClick={createComplex}>Kompleksi yayımla</Button></div></section>
    </div>
    <div className="overflow-hidden rounded-2xl border border-border/60 bg-surface"><table className="w-full text-sm"><thead><tr className="border-b text-left text-foreground/50"><th className="p-4">Kompleks</th><th>Developer</th><th>Ünvan</th><th>Status</th></tr></thead><tbody>{items.map(item=><tr key={item.id} className="border-b last:border-0"><td className="p-4 font-semibold">{item.name}</td><td>{item.developer.name}</td><td>{item.address}</td><td>{item.is_published ? "Yayımda" : "Qaralama"}</td></tr>)}</tbody></table></div>
  </div>;
}
