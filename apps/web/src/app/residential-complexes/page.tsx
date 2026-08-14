import type { Metadata } from "next";
import { Building2, Search } from "lucide-react";
import { fetchComplexes } from "@/services/development-api";
import type { ResidentialComplex } from "@/services/development-api";
import { ComplexCatalog } from "@/features/developments/complex-catalog";

export const metadata: Metadata = { title: "Yaşayış kompleksləri", description: "Yeni tikililər, mənzil planları, qiymətlər və developer təklifləri." };

export default async function ResidentialComplexesPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q = "" } = await searchParams;
  let items: ResidentialComplex[] = [];
  try { items = await fetchComplexes(q); } catch { /* empty state keeps the catalog available */ }
  return <main className="min-h-screen bg-slate-50">
    <section className="bg-slate-950 py-14 text-white"><div className="mx-auto max-w-7xl px-4">
      <p className="mb-3 flex items-center gap-2 text-sm font-semibold text-emerald-400"><Building2 className="h-5 w-5" />Birbaşa tikinti şirkətlərindən</p>
      <h1 className="text-3xl font-black sm:text-5xl">Yaşayış kompleksləri</h1><p className="mt-4 max-w-2xl text-slate-300">Planları, təhvil tarixini, kredit şərtlərini və aktual qiymətləri bir yerdə müqayisə edin.</p>
      <form className="mt-8 flex max-w-2xl rounded-xl bg-white p-2"><Search className="ml-3 mt-3 h-5 w-5 text-slate-400" /><input name="q" defaultValue={q} placeholder="Kompleks və ya ünvan axtarın" className="min-w-0 flex-1 px-3 text-slate-900 outline-none"/><button className="rounded-lg bg-emerald-600 px-6 py-3 font-bold hover:bg-emerald-700">Axtar</button></form>
    </div></section>
    <section className="mx-auto max-w-7xl px-4 py-10">
      {items.length ? <ComplexCatalog items={items} /> : <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-16 text-center"><Building2 className="mx-auto h-12 w-12 text-slate-300"/><h2 className="mt-4 text-xl font-bold">Komplekslər hazırlanır</h2><p className="mt-2 text-slate-500">Admin paneldən ilk yaşayış kompleksini əlavə edin.</p></div>}
    </section>
  </main>;
}
