import type { Metadata } from "next";
import { Suspense } from "react";
import { FavoritesList } from "@/features/favorites/favorites-list";

export const metadata: Metadata = {
  title: "Seçilmişlər",
  description: "Seçdiyiniz daşınmaz əmlak elanları."
};

export default function FavoritesPage() {
  return (
    <div className="mx-auto max-w-[1200px] px-4 py-8 lg:px-6">
      <Suspense fallback={null}>
        <FavoritesList />
      </Suspense>
    </div>
  );
}
