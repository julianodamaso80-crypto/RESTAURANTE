"use client";

import { useState } from "react";
import { X, ChevronRight, XCircle } from "lucide-react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/Button";
import { formatCurrency, formatDate } from "@/lib/utils";
import { advanceOrderStatus, cancelOrder } from "@/hooks/useOrders";
import type { Order, OrderStatus } from "@/types/api";

const NEXT_STATUS: Partial<Record<OrderStatus, { label: string; next: string }>> = {
  PENDING: { label: "Confirmar pedido", next: "CONFIRMED" },
  CONFIRMED: { label: "Iniciar preparo", next: "IN_PREPARATION" },
  IN_PREPARATION: { label: "Marcar como pronto", next: "READY" },
  READY: { label: "Despachar", next: "DISPATCHED" },
  DISPATCHED: { label: "Marcar entregue", next: "DELIVERED" },
};

const CANCELLABLE: OrderStatus[] = ["PENDING", "CONFIRMED", "IN_PREPARATION"];

export function OrderDetailDrawer({
  order,
  onClose,
  onUpdate,
}: {
  order: Order;
  onClose: () => void;
  onUpdate: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const advance = NEXT_STATUS[order.status];

  async function handleAdvance() {
    if (!advance) return;
    setLoading(true);
    try {
      await advanceOrderStatus(order.id, advance.next);
      onUpdate();
    } finally {
      setLoading(false);
    }
  }

  async function handleCancel() {
    if (!confirm("Cancelar este pedido?")) return;
    setLoading(true);
    try {
      await cancelOrder(order.id);
      onUpdate();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end animate-fade-in">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-sm bg-background-secondary border-l border-border flex flex-col h-full animate-slide-in-right shadow-elevation-4">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div>
            <h2 className="font-semibold text-foreground">Pedido {order.display_id}</h2>
            <p className="text-muted text-xs mt-0.5">{formatDate(order.created_at)}</p>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg text-muted hover:text-foreground hover:bg-surface transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Status */}
        <div className="px-5 py-3 border-b border-border">
          <StatusBadge status={order.status} />
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto p-5">
          <div className="space-y-3">
            {order.items?.map((item) => (
              <div key={item.id} className="flex items-start justify-between gap-2">
                <div className="flex gap-2.5">
                  <span className="text-primary font-semibold text-sm w-6 text-right shrink-0 tabular-nums">
                    {item.quantity}x
                  </span>
                  <p className="text-foreground text-sm">{item.name}</p>
                </div>
                <span className="text-muted-light text-sm shrink-0 tabular-nums">
                  {formatCurrency(item.total_price)}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-5 pt-4 border-t border-border flex justify-between">
            <span className="text-muted text-sm">Total</span>
            <span className="font-semibold text-primary text-base tabular-nums">{formatCurrency(order.total)}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="p-5 border-t border-border space-y-2.5">
          {advance && (
            <Button onClick={handleAdvance} loading={loading} className="w-full" size="lg" icon={<ChevronRight className="w-4 h-4" />}>
              {advance.label}
            </Button>
          )}
          {CANCELLABLE.includes(order.status) && (
            <Button variant="danger" onClick={handleCancel} disabled={loading} className="w-full" size="md" icon={<XCircle className="w-4 h-4" />}>
              Cancelar pedido
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
