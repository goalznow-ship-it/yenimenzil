'use client';

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { SearchBar } from "@/features/search/search-bar";
import Link from "next/link";

export default function HeroClient() {
  const searchParams = useSearchParams();
  const saleParams = new URLSearchParams(searchParams);
  saleParams.set("deal", "sale");
  const rentParams = new URLSearchParams(searchParams);
  rentParams.set("deal", "rent");
  const dailyParams = new URLSearchParams(searchParams);
  dailyParams.set("deal", "daily");

  return (
    <div className="flex flex-col">
      <div className="flex space-x-2 mb-4">
        <Link
          href={`/search?${saleParams.toString()}`}
          className="px-4 py-2 bg-brand text-white rounded hover:bg-brand-hover"
        >
          Alış
        </Link>
        <Link
          href={`/search?${rentParams.toString()}`}
          className="px-4 py-2 bg-border text-brand rounded hover:bg-brand-hover"
        >
          Kirayə
        </Link>
        <Link
          href={`/search?${dailyParams.toString()}`}
          className="px-4 py-2 bg-border text-brand rounded hover:bg-brand-hover"
        >
          Günlük
        </Link>
      </div>
      <SearchBar />
    </div>
  );
}
