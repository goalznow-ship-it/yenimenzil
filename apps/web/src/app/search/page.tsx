import type { Metadata } from "next";
import { Suspense } from "react";
import { SearchClient, SearchResultsSkeleton } from "@/features/search/search-client";

export const metadata: Metadata = {
  title: "Elan axtarışı",
  description:
    "Azərbaycan üzrə mənzil, kirayə, villa, torpaq və digər daşınmaz əmlak elanlarını axtar."
};

export default function SearchPage() {
  return (
    <div className="pt-4 lg:pt-6">
      <Suspense fallback={<SearchResultsSkeleton />}>
        <SearchClient />
      </Suspense>
    </div>
  );
}
