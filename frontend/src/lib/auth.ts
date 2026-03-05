import api from "./api";
import type { AuthTokens } from "@/types/api";

export async function login(
  email: string,
  password: string
): Promise<AuthTokens> {
  const { data } = await api.post<AuthTokens>("/api/v1/auth/login/", {
    email,
    password,
  });
  return data;
}

export async function refreshToken(refresh: string): Promise<{ access: string }> {
  const { data } = await api.post<{ access: string }>(
    "/api/v1/auth/refresh/",
    { refresh }
  );
  return data;
}
