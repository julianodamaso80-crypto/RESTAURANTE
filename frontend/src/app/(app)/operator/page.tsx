"use client";

import { useOrders } from "@/hooks/useOrders";
import { OrderColumn } from "@/components/operator/OrderColumn";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/shared/MetricCard";
import { ShoppingCart, Clock, CheckCircle, RefreshCw } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

const KANBAN_COLUMNS = ["PENDING", "CONFIRMED", "IN_PREPARATION", "READY", "DISPATCHED"];

export default function OperatorPage() {
  const { orders, loading, refresh } = useOrders();

  const pending = orders.filter((o) => o.status === "PENDING").length;
  const active = orders.filter((o) => !["DELIVERED", "CANCELLED"].includes(o.status)).length;
  const todayRevenue = orders
    .filter((o) => o.status === "DELIVERED")
    .reduce((sum, o) => sum + parseFloat(o.total || "0"), 0);

  return (
    <div className="flex flex-col h-full">
      <Header title="Operador // Pedidos" />

      <div className="grid grid-cols-3 gap-3 p-4 border-b border-border">
        <MetricCard label="Aguardando" value={pending} icon={Clock} accent={pending > 0 ? "yellow" : "default"} />
        <MetricCard label="Em aberto" value={active} icon={ShoppingCart} />
        <MetricCard label="Hoje" value={formatCurrency(todayRevenue)} icon={CheckCircle} accent="green" />
      </div>

      <div className="flex items-center justify-between px-4 py-2 border-b border-border">
        <span className="font-mono text-muted text-xs">Polling 10s</span>
        <button onClick={() => refresh()} className="text-muted hover:text-foreground transition-colors">
          <RefreshCw size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-x-auto p-4">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted font-mono text-sm animate-pulse">Carregando pedidos...</p>
          </div>
        ) : (
          <div className="flex gap-4" style={{ minWidth: "max-content" }}>
            {KANBAN_COLUMNS.map((status) => (
              <OrderColumn
                key={status}
                status={status}
                orders={orders.filter((o) => o.status === status)}
                onUpdate={refresh}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
