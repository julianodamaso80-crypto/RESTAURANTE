import { OrderCard } from "./OrderCard";
import type { Order, OrderStatus } from "@/types/api";

const COLUMN_CONFIG: Partial<Record<OrderStatus, { label: string; color: string }>> = {
  PENDING: { label: "Novos", color: "text-yellow-500" },
  CONFIRMED: { label: "Confirmados", color: "text-blue-500" },
  IN_PREPARATION: { label: "Preparando", color: "text-purple-400" },
  READY: { label: "Prontos", color: "text-success" },
  DISPATCHED: { label: "Despachados", color: "text-accent" },
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
    <div className="flex flex-col min-w-[260px] max-w-[280px]">
      <div className="flex items-center gap-2 mb-3">
        <h2 className={`font-mono font-bold text-xs uppercase tracking-widest ${config.color}`}>
          {config.label}
        </h2>
        <span className="font-mono text-xs text-muted bg-surface-2 px-2 py-0.5 rounded">
          {orders.length}
        </span>
      </div>
      <div className="space-y-2">
        {orders.map((order) => (
          <OrderCard key={order.id} order={order} onUpdate={onUpdate} />
        ))}
        {orders.length === 0 && (
          <div className="border border-dashed border-border rounded p-4 flex items-center justify-center">
            <p className="text-muted font-mono text-xs">Vazio</p>
          </div>
        )}
      </div>
    </div>
  );
}
