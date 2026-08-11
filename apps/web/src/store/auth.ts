"use client";

/**
 * Global auth state: the user object (from /auth/me) and login/register/
 * logout actions. The store survives page navigation; it's hydrated once
 * on the first render after mount.
 */
import { create } from "zustand";
import { authApi, type RegisterInput, type User } from "@/services/auth-api";

export const STAFF_ROLES = ["moderator", "admin", "super_admin"] as const;

interface AuthState {
  user: User | null;
  status: "loading" | "authenticated" | "guest";
  hydrated: boolean;
  loginError: string | null;
  registerError: string | null;
  hydrate: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  status: "loading",
  hydrated: false,
  loginError: null,
  registerError: null,

  hydrate: async () => {
    if (typeof window === "undefined") return;
    try {
      const user = await authApi.me();
      set({ user, status: "authenticated", hydrated: true });
    } catch {
      set({ user: null, status: "guest", hydrated: true });
    }
  },

  login: async (email, password) => {
    try {
      const { user } = await authApi.login(email, password);
      set({ user, status: "authenticated", loginError: null });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Giriş uğursuz oldu";
      set({ loginError: message });
      throw err;
    }
  },

  register: async (input) => {
    try {
      const { user } = await authApi.register(input);
      set({ user, status: "authenticated", registerError: null });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Qeydiyyat uğursuz oldu";
      set({ registerError: message });
      throw err;
    }
  },

  logout: async () => {
    try {
      await authApi.logout();
    } finally {
      set({ user: null, status: "guest" });
    }
  },

  setUser: (user) => set({ user })
}));

export function isStaff(role?: string): boolean {
  return role ? (STAFF_ROLES as readonly string[]).includes(role) : false;
}
