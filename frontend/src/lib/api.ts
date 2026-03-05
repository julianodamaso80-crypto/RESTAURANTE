import axios from "axios";
import { useAuthStore } from "@/store/auth";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const { access_token, tenantId, storeId } = useAuthStore.getState();

  if (access_token) {
    config.headers.Authorization = `Bearer ${access_token}`;
  }
  if (tenantId) {
    config.headers["X-Tenant-ID"] = tenantId;
  }
  if (storeId) {
    config.headers["X-Store-ID"] = storeId;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const { refresh_token, setTokens, logout } = useAuthStore.getState();

      if (!refresh_token) {
        logout();
        window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(
          `${api.defaults.baseURL}/api/v1/auth/refresh/`,
          { refresh: refresh_token }
        );

        setTokens(data.access, refresh_token);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch {
        logout();
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
