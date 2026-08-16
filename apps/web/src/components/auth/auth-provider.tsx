"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/store/auth";
import { useFavoritesStore } from "@/stores/favorites-store";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const hydrate = useAuth((s) => s.hydrate);
  const hydrateFavorites = useFavoritesStore((s) => s.hydrate);
  const status = useAuth((s) => s.status);

  React.useEffect(() => {
    void hydrate();
  }, [hydrate]);

  React.useEffect(() => {
    if (status === "authenticated") {
      void hydrateFavorites();
    }
  }, [status, hydrateFavorites]);

  return children;
}

/** Redirects to /login if the user is not authenticated. */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const status = useAuth((s) => s.status);
  const hydrated = useAuth((s) => s.hydrated);
  const router = useRouter();

  React.useEffect(() => {
    if (hydrated && status !== "authenticated") {
      router.replace("/login?next=" + encodeURIComponent(window.location.pathname));
    }
  }, [hydrated, status, router]);

  if (!hydrated || status !== "authenticated") {
    return (
      <div className="flex min-h-[60dvh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand/20 border-t-brand" />
      </div>
    );
  }
  return children;
}
