import type { Metadata } from "next";
import Link from "next/link";
import { Building2, CheckCircle2, Search } from "lucide-react";
import { fetchAgencyDirectory } from "@/services/agency-directory-api";

export const metadata: Metadata = {
  title: "Əmlak agentlikləri",
  description: "Azərbaycanda təsdiqlənmiş daşınmaz əmlak agentlikləri və onların təklifləri."
};

export default async function AgenciesPage() {
  const agencies = await fetchAgencyDirectory(100);
  return <main className="mx-auto min-h-[70vh] max-w-6xl px-4 py-9 lg:px-6">
    <div className="flex flex-col justify-between gap-4 border-b border-border pb-7 sm:flex-row sm:items-end">
      <div><p className="text-sm font-semibold text-brand">Peşəkar tərəfdaşlar</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">Əmlak agentlikləri</h1><p className="mt-2 text-sm text-muted-foreground">Təsdiqlənmiş agentlikləri və onların aktual təkliflərini kəşf edin.</p></div>
      <Link href="/search" className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white"><Search className="h-4 w-4"/> Elanlarda axtar</Link>
    </div>
    {agencies.length ? <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{agencies.map((agency) => <Link key={agency.id} href={`/agencies/${agency.id}`} className="group rounded-2xl border border-border bg-surface p-5 shadow-sm transition hover:-translate-y-1 hover:border-brand/30 hover:shadow-card">
      <div className="flex items-start gap-4"><div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-brand-soft text-brand">{agency.logo_url ? <img src={agency.logo_url} alt={agency.name} className="h-full w-full object-cover"/> : <Building2 className="h-8 w-8"/>}</div><div className="min-w-0"><h2 className="flex items-center gap-1.5 font-semibold">{agency.name}{agency.is_verified ? <CheckCircle2 className="h-4 w-4 shrink-0 text-brand"/> : null}</h2><p className="mt-1 line-clamp-3 text-sm leading-relaxed text-muted-foreground">{agency.description ?? "Daşınmaz əmlak üzrə peşəkar xidmətlər və aktual təkliflər."}</p></div></div>
      <div className="mt-5 border-t border-border pt-4 text-sm font-semibold text-brand">Agentliyin təkliflərinə bax →</div>
    </Link>)}</div> : <div className="mt-10 rounded-2xl border border-dashed border-border p-12 text-center text-muted-foreground">Hazırda aktiv agentlik yoxdur.</div>}
  </main>;
}
