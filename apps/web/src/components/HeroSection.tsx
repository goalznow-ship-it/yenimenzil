'use client';

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { SearchBar } from "@/features/search/search-bar";

export default function HeroSection() {
  const searchParams = useSearchParams();
  const saleParams = new URLSearchParams(searchParams);
  saleParams.set("deal", "sale");
  const rentParams = new URLSearchParams(searchParams);
  rentParams.set("deal", "rent");
  const dailyParams = new URLSearchParams(searchParams);
  dailyParams.set("deal", "daily");

  return (
    <div className="mb-12">
      <div className="mb-6 max-w-3xl">
        <h1 className="mb-3 text-5xl font-bold tracking-tight text-foreground leading-tight">
          Yeni məkanını burada tap.
        </h1>
        <p className="text-xl leading-relaxed text-muted-foreground">
          Azərbaycan üzrə mənzil, villa, torpaq, obyekt və digər daşınmaz əmlak elanlarını rahat şəkildə kəşf et.
        </p>
      </div>
      <div className="rounded-2xl border border-border bg-surface p-1 shadow-xl md:p-1.5">
        <SearchBar />
      </div>
    </div>
  );
}