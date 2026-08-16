import { create } from "zustand";
import { persist } from "zustand/middleware";
import { dashboardApi } from "@/services/dashboard-api";
import { useAuth } from "@/store/auth";

interface FavoritesState {
  ids: string[];
  hydrated: boolean;
  hydrate: () => Promise<void>;
  toggle: (id: string) => void;
  remove: (id: string) => void;
  has: (id: string) => boolean;
  clear: () => void;
}

function isAuthenticated() {
  return useAuth.getState().status === "authenticated";
}

export const useFavoritesStore = create<FavoritesState>()(
  persist(
    (set, get) => ({
      ids: [],
      hydrated: false,

      hydrate: async () => {
        if (!isAuthenticated()) return;
        await Promise.resolve();
        try {
          const favorites = await dashboardApi.favorites();
          set({ ids: favorites.map((f) => f.id), hydrated: true });
        } catch {
          set({ hydrated: true });
        }
      },

      toggle: (id) => {
        const { ids, remove } = get();
        if (ids.includes(id)) {
          remove(id);
          return;
        }
        set((state) => ({ ids: [...state.ids, id] }));
        if (isAuthenticated()) {
          void dashboardApi.addFavorite(id).catch(() => {});
        }
      },

      remove: (id) => {
        set((state) => ({ ids: state.ids.filter((x) => x !== id) }));
        if (isAuthenticated()) {
          void dashboardApi.removeFavorite(id).catch(() => {});
        }
      },

      has: (id) => get().ids.includes(id),

      clear: () => set({ ids: [] })
    }),
    {
      name: "yenimenzil-favorites",
      partialize: (state) => ({ ids: state.ids })
    }
  )
);