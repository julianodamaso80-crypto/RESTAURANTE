"use client";

import { cn } from "@/lib/utils";
import type { OrderStatus } from "@/types/api";

const STATUS_CONFIG: Record<OrderStatus, { label: string; className: string }> = {
  PENDING: {
    label: "Pendente",
    className: "bg-yellow-500/15 text-yellow-500 border-yellow-500/30",
  },
  CONFIRMED: {
    label: "Confirmado",
    className: "bg-blue-500/15 text-blue-500 border-blue-500/30",
  },
  IN_PREPARATION: {
    label: "Preparando",
    className: "bg-purple-500/15 text-purple-500 border-purple-500/30",
  },
  READY: {
    label: "Pronto",
    className: "bg-green-500/15 text-green-500 border-green-500/30",
  },
  DISPATCHED: {
    label: "Despachado",
    className: "bg-orange-500/15 text-orange-500 border-orange-500/30",
  },
  DELIVERED: {
    label: "Entregue",
    className: "bg-emerald-500/15 text-emerald-500 border-emerald-500/30",
  },
  CANCELLED: {
    label: "Cancelado",
    className: "bg-red-500/15 text-red-500 border-red-500/30",
  },
};

interface StatusBadgeProps {
  status: OrderStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.PENDING;

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 text-xs font-mono font-medium rounded border",
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  );
}
