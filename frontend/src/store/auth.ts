import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types/api";

interface AuthState {
  access_token: string | null;
  refresh_token: string | null;
  user: User | null;
  tenantId: string | null;
  storeId: string | null;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User) => void;
  setTenant: (tenantId: string) => void;
  setStore: (storeId: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      access_token: null,
      refresh_token: null,
      user: null,
      tenantId: null,
      storeId: null,
      setTokens: (access, refresh) =>
        set({ access_token: access, refresh_token: refresh }),
      setUser: (user) => set({ user }),
      setTenant: (tenantId) => set({ tenantId }),
      setStore: (storeId) => set({ storeId }),
      logout: () =>
        set({
          access_token: null,
          refresh_token: null,
          user: null,
          tenantId: null,
          storeId: null,
        }),
    }),
    { name: "auth-storage" }
  )
);
