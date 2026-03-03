import useSWR from "swr";
import api from "@/lib/api";
import type { Order } from "@/types/api";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

export function useOrders() {
  const { data, error, mutate } = useSWR<{ results: Order[] }>(
    "/orders/?status=PENDING,CONFIRMED,IN_PREPARATION,READY,DISPATCHED",
    fetcher,
    { refreshInterval: 10000 }
  );

  return {
    orders: data?.results ?? [],
    loading: !data && !error,
    error,
    refresh: mutate,
  };
}

export async function advanceOrderStatus(orderId: string, nextStatus: string) {
  return api.post(`/orders/${orderId}/advance/`, { status: nextStatus });
}

export async function cancelOrder(orderId: string) {
  return api.post(`/orders/${orderId}/cancel/`, { reason: "Cancelado pelo operador" });
}
