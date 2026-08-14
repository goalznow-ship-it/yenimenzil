import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Building2, CalendarDays, CheckCircle2, MapPin, Phone, Ruler, ShieldCheck } from "lucide-react";
import { fetchComplex } from "@/services/development-api";

const money = (value?: number | null) => value == null ? "Sorğu ilə" : `${new Intl.NumberFormat("az-AZ").format(value)} AZN`;
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> { try { const item = await fetchComplex((await params).slug); return { title: item.name, description: item.description?.slice(0, 155) ?? item.address }; } catch { return { title: "Yaşayış kompleksi" }; } }

export default async function ComplexDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  let item; try { item = await fetchComplex((await params).slug); } catch { notFound(); }
  return <main className="min-h-screen bg-slate-50 pb-16">
    <div className="relative h-[420px] bg-slate-900">{item.cover_url ? <img src={item.cover_url} alt={item.name} className="h-full w-full object-cover opacity-70"/> : <Building2 className="absolute inset-0 m-auto h-28 w-28 text-white/20"/>}<div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950 p-8 text-white"><div className="mx-auto max-w-7xl"><p className="flex items-center gap-2 text-emerald-300">{item.developer.is_verified && <ShieldCheck className="h-5 w-5"/>}{item.developer.name}</p><h1 className="mt-2 text-4xl font-black sm:text-6xl">{item.name}</h1><p className="mt-3 flex items-center gap-2 text-slate-200"><MapPin className="h-5 w-5"/>{item.address}</p></div></div></div>
    <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 lg:grid-cols-[1fr_360px]">
      <div className="space-y-8">
        <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-xl bg-white p-4 shadow-sm"><Building2 className="mb-3 h-6 w-6 text-emerald-600"/><p className="font-semibold">{item.buildings_count ?? "—"} bina</p></div>
          <div className="rounded-xl bg-white p-4 shadow-sm"><Ruler className="mb-3 h-6 w-6 text-emerald-600"/><p className="font-semibold">{item.price_per_sqm_from ? `${money(item.price_per_sqm_from)}/m²` : "Qiymət sorğu ilə"}</p></div>
          <div className="rounded-xl bg-white p-4 shadow-sm"><CalendarDays className="mb-3 h-6 w-6 text-emerald-600"/><p className="font-semibold">{item.delivery_date ? new Date(item.delivery_date).toLocaleDateString("az-AZ") : "Təhvil verilib"}</p></div>
          <div className="rounded-xl bg-white p-4 shadow-sm"><MapPin className="mb-3 h-6 w-6 text-emerald-600"/><p className="font-semibold">{item.district ?? item.city}</p></div>
        </section>
        <section className="rounded-2xl bg-white p-6 shadow-sm"><h2 className="text-2xl font-bold">Kompleks haqqında</h2><p className="mt-4 whitespace-pre-line leading-7 text-slate-600">{item.description ?? "Ətraflı məlumat tezliklə əlavə ediləcək."}</p></section>
        <section className="rounded-2xl bg-white p-6 shadow-sm"><h2 className="text-2xl font-bold">Mənzil seçimləri</h2><div className="mt-5 overflow-x-auto"><table className="w-full text-left"><thead className="border-b text-sm text-slate-500"><tr><th className="py-3">Otaq</th><th>Sahə</th><th>Qiymət</th><th>Mövcud</th></tr></thead><tbody>{item.unit_types.map(unit=><tr key={unit.id} className="border-b last:border-0"><td className="py-4 font-bold">{unit.rooms} otaq</td><td>{unit.area_from}{unit.area_to ? `–${unit.area_to}`:""} m²</td><td className="font-semibold text-emerald-700">{money(unit.price_from)}</td><td>{unit.available_count}</td></tr>)}</tbody></table></div></section>
        {!!item.amenities.length && <section className="rounded-2xl bg-white p-6 shadow-sm"><h2 className="text-2xl font-bold">Üstünlüklər</h2><div className="mt-5 grid gap-3 sm:grid-cols-2">{item.amenities.map(x=><p key={x} className="flex items-center gap-2"><CheckCircle2 className="h-5 w-5 text-emerald-600"/>{x}</p>)}</div></section>}
      </div>
      <aside><div className="sticky top-24 rounded-2xl bg-white p-6 shadow-lg"><p className="text-sm text-slate-500">Mənzillər</p><p className="mt-1 text-3xl font-black text-emerald-700">{money(item.min_price)}-dən</p>{item.payment_terms && <p className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-900">{item.payment_terms}</p>}<a href={item.developer.phone ? `tel:${item.developer.phone}` : "#"} className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 px-5 py-4 font-bold text-white hover:bg-emerald-700"><Phone className="h-5 w-5"/>Satış ofisi ilə əlaqə</a><p className="mt-4 text-center text-xs text-slate-500">Sorğunuz birbaşa təsdiqlənmiş developerə göndərilir.</p></div></aside>
    </div>
  </main>;
}
