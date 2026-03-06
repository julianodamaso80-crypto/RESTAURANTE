"use client";

import useSWR from "swr";
import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Crown } from "lucide-react";
import type { Customer, PaginatedResponse } from "@/types/api";

export function TopCustomers() {
  const { data } = useSWR<PaginatedResponse<Customer>>(
    "/customers/?ordering=-rfv_monetary_cents&page_size=5",
    (url: string) => api.get(url).then((r) => r.data)
  );
  const customers = data?.results ?? [];

  return (
    <div className="bg-background-secondary border border-border rounded-lg shadow-card p-5">
      <div className="flex items-center gap-2 mb-3">
        <Crown size={14} className="text-warning" />
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wider">
          Top Clientes
        </h3>
      </div>
      <div className="space-y-2">
        {customers.map((customer, i) => (
          <div key={customer.id} className="flex items-center gap-3">
            <span className="text-muted text-xs tabular-nums w-4">
              {i + 1}.
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-foreground text-sm truncate">
                {customer.name || customer.phone}
              </p>
              <p className="text-muted text-xs tabular-nums">
                {customer.rfv_frequency ?? 0} pedidos
              </p>
            </div>
            <span className="text-warning text-xs tabular-nums shrink-0">
              {formatCurrency((customer.rfv_monetary_cents ?? 0) / 100)}
            </span>
          </div>
        ))}
        {customers.length === 0 && (
          <p className="text-muted text-xs">Sem dados</p>
        )}
      </div>
    </div>
  );
}
