"use client";

import { useAuthStore } from "@/store/auth";

export function useStore() {
  const { tenantId, storeId, setTenant, setStore } = useAuthStore();

  return {
    tenantId,
    storeId,
    setTenant,
    setStore,
  };
}
