"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle2, Clock, ChefHat, Truck, Package, Loader2 } from "lucide-react";
import { formatCents, cn } from "@/lib/utils";
import type { PublicOrder, OrderStatus } from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STATUS_STEPS: { status: OrderStatus; label: string; icon: typeof Clock }[] = [
  { status: "PENDING", label: "Recebido", icon: Clock },
  { status: "CONFIRMED", label: "Confirmado", icon: CheckCircle2 },
  { status: "IN_PREPARATION", label: "Em preparo", icon: ChefHat },
  { status: "READY", label: "Pronto", icon: Package },
  { status: "DISPATCHED", label: "Saiu para entrega", icon: Truck },
  { status: "DELIVERED", label: "Entregue", icon: CheckCircle2 },
];

function getStatusIndex(status: OrderStatus): number {
  const idx = STATUS_STEPS.findIndex((s) => s.status === status);
  return idx >= 0 ? idx : 0;
}

export default function OrderTrackingPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.orderId as string;

  const [order, setOrder] = useState<PublicOrder | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchOrder = useCallback(async () => {
    try {
      const res = await fetch(`${BASE_URL}/api/v1/orders/public/${orderId}/`);
      if (!res.ok) {
        setError("Pedido nao encontrado.");
        setLoading(false);
        return;
      }
      const data = await res.json();
      setOrder(data);
      setLoading(false);
    } catch {
      setError("Erro ao carregar pedido.");
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    fetchOrder();
    const interval = setInterval(fetchOrder, 15000);
    return () => clearInterval(interval);
  }, [fetchOrder]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-primary" />
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4">
        <p className="text-red-400">{error || "Pedido nao encontrado."}</p>
        <button onClick={() => router.push("/")} className="text-primary text-sm underline">
          Voltar
        </button>
      </div>
    );
  }

  const currentIndex = getStatusIndex(order.status);
  const isCancelled = order.status === "CANCELLED";
  const isFinal = order.status === "DELIVERED" || isCancelled;

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="px-4 py-8 text-center border-b border-border">
        <div className="inline-flex items-center gap-2 bg-primary/10 border border-primary/30 rounded-full px-4 py-2 mb-3">
          <CheckCircle2 size={16} className="text-primary" />
          <span className="text-primary font-semibold text-sm">
            {isCancelled ? "Pedido cancelado" : isFinal ? "Pedido entregue" : "Pedido recebido!"}
          </span>
        </div>
        <h1 className="font-semibold text-2xl text-foreground">
          Pedido {order.display_number}
        </h1>
        {!isFinal && (
          <p className="text-muted text-sm mt-1">
            Tempo estimado: 30-45 minutos
          </p>
        )}
      </div>

      <div className="max-w-lg mx-auto px-4 py-8 space-y-8">
        {/* Status tracker */}
        {!isCancelled && (
          <div className="space-y-0">
            {STATUS_STEPS.map((stepInfo, idx) => {
              const isActive = idx <= currentIndex;
              const isCurrent = idx === currentIndex;
              const Icon = stepInfo.icon;
              return (
                <div key={stepInfo.status} className="flex items-start gap-3">
                  <div className="flex flex-col items-center">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center border-2",
                        isCurrent
                          ? "bg-primary border-primary text-white"
                          : isActive
                            ? "bg-primary/20 border-primary text-primary"
                            : "bg-background-secondary border-border text-muted",
                      )}
                    >
                      <Icon size={14} />
                    </div>
                    {idx < STATUS_STEPS.length - 1 && (
                      <div
                        className={cn(
                          "w-0.5 h-6",
                          isActive ? "bg-primary/40" : "bg-surface",
                        )}
                      />
                    )}
                  </div>
                  <div className="pt-1">
                    <span
                      className={cn(
                        "text-sm font-semibold",
                        isActive ? "text-foreground" : "text-muted",
                      )}
                    >
                      {stepInfo.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {isCancelled && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-center">
            <p className="text-red-400 font-semibold">Este pedido foi cancelado.</p>
          </div>
        )}

        {/* Order items */}
        <div>
          <h2 className="text-foreground-secondary font-semibold text-sm mb-3">Itens do pedido</h2>
          <div className="space-y-2">
            {order.items.map((item) => (
              <div key={item.id} className="flex justify-between items-start bg-background-secondary border border-border rounded-lg p-3.5">
                <div>
                  <span className="text-foreground text-sm">
                    {item.quantity}x {item.name}
                  </span>
                  {item.notes && (
                    <p className="text-muted text-xs mt-0.5">{item.notes}</p>
                  )}
                </div>
                <span className="tabular-nums text-primary text-sm font-semibold">
                  {formatCents(item.total_cents)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Totals */}
        <div className="border-t border-border pt-4 space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted">Subtotal</span>
            <span className="tabular-nums text-foreground">{formatCents(order.subtotal_cents)}</span>
          </div>
          {order.delivery_fee_cents > 0 && (
            <div className="flex justify-between text-sm">
              <span className="text-muted">Taxa de entrega</span>
              <span className="tabular-nums text-foreground">{formatCents(order.delivery_fee_cents)}</span>
            </div>
          )}
          <div className="flex justify-between font-semibold pt-1">
            <span className="text-foreground-secondary">Total</span>
            <span className="tabular-nums text-primary text-lg">{formatCents(order.total_cents)}</span>
          </div>
        </div>

        {/* Back button */}
        <button
          onClick={() => router.push("/")}
          className="w-full bg-surface/50 border border-border text-foreground-secondary font-semibold py-3 rounded-lg text-sm hover:border-primary transition-colors"
        >
          Voltar ao cardapio
        </button>
      </div>
    </div>
  );
}
