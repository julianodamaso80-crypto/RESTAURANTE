import useSWR from "swr";
import axios from "axios";
import type { PublicCatalog } from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const publicFetcher = (url: string) =>
  axios.get<PublicCatalog>(`${BASE_URL}/api/v1${url}`).then((r) => r.data);

export function usePublicCatalog(catalogId: string) {
  const { data, error } = useSWR(
    catalogId ? `/catalogs/${catalogId}/public/` : null,
    publicFetcher,
    { revalidateOnFocus: false },
  );
  return {
    catalog: data ?? null,
    categories: data?.categories ?? [],
    loading: !data && !error,
    error,
  };
}
