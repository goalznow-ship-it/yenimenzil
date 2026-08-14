"use client";
import * as React from "react";
import { useRouter } from "next/navigation";
import { Grid2X2, Map } from "lucide-react";
import { ComplexCard } from "./complex-card";
import { MapView } from "@/features/map/map-view";
import type { ResidentialComplex } from "@/services/development-api";

export function ComplexCatalog({ items }: { items: ResidentialComplex[] }) {
  const [view, setView] = React.useState<"list" | "map">("list");
  const router = useRouter();
  const mapped = items.filter((item) => item.latitude != null && item.longitude != null);
  const markers = mapped.map((item) => ({ id: item.id, point: { lat: Number(item.latitude), lng: Number(item.longitude) }, price: item.min_price ?? 0, formattedPrice: item.min_price ? `${Number(item.min_price).toLocaleString("az-AZ")} ${item.currency}-dən` : item.name }));
  return <><div className="mb-6 flex items-center justify-between gap-3"><h2 className="text-2xl font-bold text-slate-900">{items.length} kompleks</h2><div className="flex rounded-xl border bg-white p-1"><button onClick={() => setView("list")} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold ${view === "list" ? "bg-emerald-600 text-white" : "text-slate-600"}`}><Grid2X2 className="h-4 w-4"/>Siyahı</button><button onClick={() => setView("map")} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold ${view === "map" ? "bg-emerald-600 text-white" : "text-slate-600"}`}><Map className="h-4 w-4"/>Xəritə</button></div></div>{view === "map" ? <MapView className="h-[620px] overflow-hidden rounded-2xl border" markers={markers} center={{lat:40.4093,lng:49.8671}} zoom={10.5} onMarkerClick={(marker) => { const item=mapped.find((entry)=>entry.id===marker.id); if(item) router.push(`/residential-complexes/${item.slug}`); }}/> : <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">{items.map((item)=><ComplexCard key={item.id} item={item}/>)}</div>}</>;
}
