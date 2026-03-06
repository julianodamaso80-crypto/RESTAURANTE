import { OrderCard } from "./OrderCard";
import type { Order, OrderStatus } from "@/types/api";

const COLUMN_CONFIG: Partial<Record<OrderStatus, { label: string; color: string; bg: string }>> = {
  PENDING: { label: "Novos", color: "text-amber-400", bg: "bg-amber-500/10" },
  CONFIRMED: { label: "Confirmados", color: "text-blue-400", bg: "bg-blue-500/10" },
  IN_PREPARATION: { label: "Preparando", color: "text-violet-400", bg: "bg-violet-500/10" },
  READY: { label: "Prontos", color: "text-emerald-400", bg: "bg-emerald-500/10" },
  DISPATCHED: { label: "Despachados", color: "text-primary", bg: "bg-primary/10" },
};

export function OrderColumn({
  status,
  orders,
  onUpdate,
}: {
  status: string;
  orders: Order[];
  onUpdate: () => void;
}) {
  const config = COLUMN_CONFIG[status as OrderStatus];
  if (!config) return null;

  return (
    <div className="flex flex-col min-w-[280px] max-w-[300px]">
      <div className="flex items-center gap-2.5 mb-3 px-1">
        <div className={`w-2 h-2 rounded-full ${config.color.replace("text-", "bg-")}`} />
        <h2 className={`font-semibold text-xs uppercase tracking-wider ${config.color}`}>
          {config.label}
        </h2>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${config.bg} ${config.color}`}>
          {orders.length}
        </span>
      </div>
      <div className="space-y-2.5">
        {orders.map((order) => (
          <OrderCard key={order.id} order={order} onUpdate={onUpdate} />
        ))}
        {orders.length === 0 && (
          <div className="border border-dashed border-border rounded-lg p-6 flex items-center justify-center">
            <p className="text-muted text-xs">Nenhum pedido</p>
          </div>
        )}
      </div>
    </div>
  );
}
