"use client";

import useSWR from "swr";
import api from "@/lib/api";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatCurrency, timeAgo } from "@/lib/utils";
import type { Order, PaginatedResponse } from "@/types/api";

export function RecentOrders() {
  const { data } = useSWR<PaginatedResponse<Order>>(
    "/orders/?ordering=-created_at&page_size=8",
    (url: string) => api.get(url).then((r) => r.data)
  );
  const orders = data?.results ?? [];

  return (
    <div className="bg-background-secondary border border-border rounded-lg shadow-card p-5">
      <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-3">
        Pedidos Recentes
      </h3>
      <div className="space-y-2">
        {orders.map((order) => (
          <div key={order.id} className="flex items-center gap-3">
            <span className="text-foreground text-xs tabular-nums w-16 shrink-0">
              {order.display_id}
            </span>
            <StatusBadge status={order.status} />
            <span className="text-primary text-xs tabular-nums ml-auto shrink-0">
              {formatCurrency(parseFloat(order.total || "0"))}
            </span>
            <span className="text-muted text-xs shrink-0">
              {timeAgo(order.created_at)}
            </span>
          </div>
        ))}
        {orders.length === 0 && (
          <p className="text-muted text-xs">Sem pedidos hoje</p>
        )}
      </div>
    </div>
  );
}
