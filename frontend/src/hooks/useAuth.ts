"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { login as loginApi } from "@/lib/auth";

export function useAuth() {
  const router = useRouter();
  const { access_token, user, setTokens, setUser, logout: storeLogout } = useAuthStore();

  const isAuthenticated = !!access_token;

  async function login(email: string, password: string) {
    const tokens = await loginApi(email, password);
    setTokens(tokens.access, tokens.refresh);

    // Decode user from JWT payload (basic decode)
    try {
      const payload = JSON.parse(atob(tokens.access.split(".")[1]));
      setUser({
        id: payload.user_id || payload.sub || "",
        email: payload.email || email,
        full_name: payload.full_name || payload.name || email,
        role: payload.role || "operator",
      });
    } catch {
      setUser({ id: "", email, full_name: email, role: "operator" });
    }

    router.push("/operator");
  }

  function logout() {
    storeLogout();
    router.push("/login");
  }

  return { isAuthenticated, user, login, logout };
}
