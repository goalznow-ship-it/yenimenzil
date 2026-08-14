import type { Metadata } from "next";
import Link from "next/link";
import { Check, Crown } from "lucide-react";

export const metadata: Metadata = { title: "Biznes paketləri", description: "Agentlik və yaşayış kompleksləri üçün YeniMenzil biznes paketləri." };
const PACKAGES = [
  {name:"Basic",price:300,listings:75,balance:150,discount:0},
  {name:"Silver",price:500,listings:150,balance:250,discount:5},
  {name:"Gold",price:1000,listings:400,balance:500,discount:10},
  {name:"Platinum",price:1500,listings:500,balance:1000,discount:15}
];
export default function BusinessPackagesPage(){return <main className="mx-auto max-w-7xl px-4 py-12"><div className="mx-auto max-w-2xl text-center"><Crown className="mx-auto h-9 w-9 text-brand"/><h1 className="mt-3 text-4xl font-bold">Biznes paketləri</h1><p className="mt-3 text-muted-foreground">Agentliklər və developer şirkətləri üçün elan, reklam balansı və premium görünürlük.</p></div><div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">{PACKAGES.map((item)=><section key={item.name} className={`rounded-2xl border bg-surface p-6 shadow-sm ${item.name==="Gold"?"border-brand ring-2 ring-brand/15":"border-border"}`}><h2 className="text-xl font-bold">{item.name}</h2><p className="mt-3 text-3xl font-bold">{item.price} AZN</p><p className="text-sm text-muted-foreground">30 gün</p><ul className="mt-6 space-y-3 text-sm"><li className="flex gap-2"><Check className="h-4 w-4 text-brand"/>{item.listings} elan balansı</li><li className="flex gap-2"><Check className="h-4 w-4 text-brand"/>{item.balance} AZN promosyon balansı</li><li className="flex gap-2"><Check className="h-4 w-4 text-brand"/>Brendləşdirilmiş profil</li><li className="flex gap-2"><Check className="h-4 w-4 text-brand"/>Prioritet dəstək</li>{item.discount?<li className="flex gap-2"><Check className="h-4 w-4 text-brand"/>Promosyonlara {item.discount}% endirim</li>:null}</ul><Link href={`/contact?subject=${item.name}%20biznes%20paketi`} className="mt-7 block rounded-xl bg-brand px-4 py-3 text-center text-sm font-bold text-white">Müraciət et</Link></section>)}</div><p className="mt-8 text-center text-sm text-muted-foreground">Paket aktivləşdirilməsi şirkət yoxlamasından sonra satış komandası tərəfindən tamamlanır.</p></main>}
