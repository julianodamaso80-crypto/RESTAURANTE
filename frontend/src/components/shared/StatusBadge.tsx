"use client";

import { Badge } from "@/components/ui/Badge";
import type { OrderStatus } from "@/types/api";

const STATUS_CONFIG: Record<OrderStatus, { label: string; variant: "warning" | "info" | "primary" | "success" | "accent" | "danger" | "default" }> = {
  PENDING: { label: "Pendente", variant: "warning" },
  CONFIRMED: { label: "Confirmado", variant: "info" },
  IN_PREPARATION: { label: "Preparando", variant: "primary" },
  READY: { label: "Pronto", variant: "success" },
  DISPATCHED: { label: "Despachado", variant: "accent" },
  DELIVERED: { label: "Entregue", variant: "success" },
  CANCELLED: { label: "Cancelado", variant: "danger" },
};

interface StatusBadgeProps {
  status: OrderStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.PENDING;

  return (
    <Badge variant={config.variant} dot className={className}>
      {config.label}
    </Badge>
  );
}
