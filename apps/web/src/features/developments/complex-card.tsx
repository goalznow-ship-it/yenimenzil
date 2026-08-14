import Link from "next/link";
import { Building2, CalendarDays, MapPin, ShieldCheck } from "lucide-react";
import type { ResidentialComplex } from "@/services/development-api";

const money = (value?: number | null) => value == null ? "Qiymət sorğu ilə" : `${new Intl.NumberFormat("az-AZ").format(value)} AZN-dən`;

export function ComplexCard({ item }: { item: ResidentialComplex }) {
  return (
    <Link href={`/residential-complexes/${item.slug}`} className="group overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-xl">
      <div className="relative h-56 overflow-hidden bg-gradient-to-br from-emerald-100 to-slate-200">
        {item.cover_url ? <img src={item.cover_url} alt={item.name} className="h-full w-full object-cover transition duration-500 group-hover:scale-105" /> : <Building2 className="absolute inset-0 m-auto h-16 w-16 text-emerald-700/30" />}
        {item.is_featured && <span className="absolute left-4 top-4 rounded-full bg-amber-400 px-3 py-1 text-xs font-bold text-slate-900">Seçilmiş kompleks</span>}
      </div>
      <div className="space-y-3 p-5">
        <div className="flex items-start justify-between gap-3">
          <div><h2 className="text-lg font-bold text-slate-900">{item.name}</h2><p className="mt-1 flex items-center gap-1 text-sm text-slate-500"><MapPin className="h-4 w-4" />{item.address}</p></div>
          {item.developer.is_verified && <ShieldCheck className="h-5 w-5 shrink-0 text-emerald-600" />}
        </div>
        <div className="flex items-center justify-between border-t border-slate-100 pt-3">
          <div><p className="font-bold text-emerald-700">{money(item.min_price)}</p><p className="text-xs text-slate-500">{item.developer.name}</p></div>
          <span className="flex items-center gap-1 text-xs text-slate-500"><CalendarDays className="h-4 w-4" />{item.delivery_date ? new Date(item.delivery_date).getFullYear() : "Təhvil verilib"}</span>
        </div>
      </div>
    </Link>
  );
}
