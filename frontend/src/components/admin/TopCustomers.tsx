"use client";

import useSWR from "swr";
import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Crown } from "lucide-react";
import type { Customer, PaginatedResponse } from "@/types/api";

export function TopCustomers() {
  const { data } = useSWR<PaginatedResponse<Customer>>(
    "/customers/?ordering=-total_spent&page_size=5",
    (url: string) => api.get(url).then((r) => r.data)
  );
  const customers = data?.results ?? [];

  return (
    <div className="bg-surface border border-border rounded p-4">
      <div className="flex items-center gap-2 mb-3">
        <Crown size={14} className="text-warning" />
        <h3 className="text-muted text-xs font-mono uppercase tracking-wider">
          Top Clientes
        </h3>
      </div>
      <div className="space-y-2">
        {customers.map((customer, i) => (
          <div key={customer.id} className="flex items-center gap-3">
            <span className="font-mono text-muted text-xs w-4">
              {i + 1}.
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-foreground text-sm truncate">
                {customer.full_name || customer.phone}
              </p>
              <p className="text-muted text-xs font-mono">
                {customer.total_orders} pedidos
              </p>
            </div>
            <span className="font-mono text-warning text-xs shrink-0">
              {formatCurrency(parseFloat(customer.total_spent || "0"))}
            </span>
          </div>
        ))}
        {customers.length === 0 && (
          <p className="text-muted text-xs font-mono">Sem dados</p>
        )}
      </div>
    </div>
  );
}
