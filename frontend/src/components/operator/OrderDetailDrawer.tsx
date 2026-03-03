"use client";

import { useState } from "react";
import { X, ChevronRight, XCircle } from "lucide-react";
import { StatusBadge } from "@/components/shared/StatusBadge";
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
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-sm bg-surface border-l border-border flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div>
            <h2 className="font-mono font-bold text-foreground">Pedido {order.display_id}</h2>
            <p className="text-muted text-xs">{formatDate(order.created_at)}</p>
          </div>
          <button onClick={onClose} className="text-muted hover:text-foreground">
            <X size={20} />
          </button>
        </div>

        {/* Status */}
        <div className="px-4 py-3 border-b border-border">
          <StatusBadge status={order.status} />
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {order.items?.map((item) => (
              <div key={item.id} className="flex items-start justify-between gap-2">
                <div className="flex gap-2">
                  <span className="font-mono text-accent font-bold text-sm w-6 text-right shrink-0">
                    {item.quantity}x
                  </span>
                  <p className="text-foreground text-sm">{item.name}</p>
                </div>
                <span className="font-mono text-muted text-sm shrink-0">
                  {formatCurrency(item.total_price)}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-border flex justify-between">
            <span className="font-mono text-muted text-sm">Total</span>
            <span className="font-mono font-bold text-accent">{formatCurrency(order.total)}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="p-4 border-t border-border space-y-2">
          {advance && (
            <button
              onClick={handleAdvance}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-accent text-black font-mono font-bold text-sm py-3 rounded hover:opacity-90 disabled:opacity-50"
            >
              <ChevronRight size={16} />
              {advance.label}
            </button>
          )}
          {CANCELLABLE.includes(order.status) && (
            <button
              onClick={handleCancel}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 border border-danger/30 text-danger font-mono text-sm py-2 rounded hover:bg-danger/10"
            >
              <XCircle size={14} />
              Cancelar pedido
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
