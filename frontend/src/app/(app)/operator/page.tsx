"use client";

import { useOrders } from "@/hooks/useOrders";
import { OrderColumn } from "@/components/operator/OrderColumn";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/shared/MetricCard";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
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
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        title="Pedidos"
        subtitle="Painel do operador"
        actions={
          <div className="flex items-center gap-2">
            <Badge variant="primary" dot>Polling 10s</Badge>
            <Button variant="ghost" size="sm" onClick={() => refresh()} icon={<RefreshCw className="w-3.5 h-3.5" />}>
              Atualizar
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-3 gap-4 p-6 pb-0">
        <MetricCard label="Aguardando" value={pending} icon={Clock} accent={pending > 0 ? "yellow" : "default"} />
        <MetricCard label="Em aberto" value={active} icon={ShoppingCart} />
        <MetricCard label="Receita hoje" value={formatCurrency(todayRevenue)} icon={CheckCircle} accent="green" />
      </div>

      <div className="flex-1 overflow-x-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-8 h-8 border-2 border-surface-2 border-t-primary rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm text-muted">Carregando pedidos...</p>
            </div>
          </div>
        ) : (
          <div className="flex gap-4 h-full" style={{ minWidth: "max-content" }}>
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
