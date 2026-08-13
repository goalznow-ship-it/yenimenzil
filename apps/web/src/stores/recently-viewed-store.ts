import { create } from "zustand";
import { persist } from "zustand/middleware";

const MAX_RECENT = 20;

interface RecentlyViewedState {
  ids: string[];
  push: (id: string) => void;
  clear: () => void;
}

export const useRecentlyViewedStore = create<RecentlyViewedState>()(
  persist(
    (set) => ({
      ids: [],
      push: (id) =>
        set((state) => ({
          ids: [id, ...state.ids.filter((x) => x !== id)].slice(0, MAX_RECENT)
        })),
      clear: () => set({ ids: [] })
    }),
    { name: "yenimenzil-recently-viewed" }
  )
);
