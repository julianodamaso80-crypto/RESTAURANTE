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
      <div className="min-h-screen bg-[#0F0A06] flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-[#F97316]" />
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="min-h-screen bg-[#0F0A06] flex flex-col items-center justify-center gap-4">
        <p className="text-red-400 font-mono">{error || "Pedido nao encontrado."}</p>
        <button onClick={() => router.push("/")} className="text-[#F97316] text-sm underline">
          Voltar
        </button>
      </div>
    );
  }

  const currentIndex = getStatusIndex(order.status);
  const isCancelled = order.status === "CANCELLED";
  const isFinal = order.status === "DELIVERED" || isCancelled;

  return (
    <div className="min-h-screen bg-[#0F0A06] text-[#FFF7ED]">
      {/* Header */}
      <div className="px-4 py-6 text-center border-b border-[#3D2B1A]">
        <div className="inline-flex items-center gap-2 bg-[#F97316]/10 border border-[#F97316]/30 rounded-full px-4 py-2 mb-3">
          <CheckCircle2 size={16} className="text-[#F97316]" />
          <span className="text-[#F97316] font-semibold text-sm">
            {isCancelled ? "Pedido cancelado" : isFinal ? "Pedido entregue" : "Pedido recebido!"}
          </span>
        </div>
        <h1 className="font-bold text-2xl text-[#FFF7ED]">
          Pedido {order.display_number}
        </h1>
        {!isFinal && (
          <p className="text-[#7C5C3E] text-sm mt-1">
            Tempo estimado: 30-45 minutos
          </p>
        )}
      </div>

      <div className="max-w-lg mx-auto px-4 py-6 space-y-6">
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
                          ? "bg-[#F97316] border-[#F97316] text-black"
                          : isActive
                            ? "bg-[#F97316]/20 border-[#F97316] text-[#F97316]"
                            : "bg-[#1A1208] border-[#3D2B1A] text-[#7C5C3E]",
                      )}
                    >
                      <Icon size={14} />
                    </div>
                    {idx < STATUS_STEPS.length - 1 && (
                      <div
                        className={cn(
                          "w-0.5 h-6",
                          isActive ? "bg-[#F97316]/40" : "bg-[#3D2B1A]",
                        )}
                      />
                    )}
                  </div>
                  <div className="pt-1">
                    <span
                      className={cn(
                        "text-sm font-semibold",
                        isActive ? "text-[#FFF7ED]" : "text-[#7C5C3E]",
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
          <div className="bg-red-900/20 border border-red-800 rounded p-4 text-center">
            <p className="text-red-400 font-semibold">Este pedido foi cancelado.</p>
          </div>
        )}

        {/* Order items */}
        <div>
          <h2 className="text-[#D6B896] font-semibold text-sm mb-3">Itens do pedido</h2>
          <div className="space-y-2">
            {order.items.map((item) => (
              <div key={item.id} className="flex justify-between items-start bg-[#1A1208] border border-[#3D2B1A] rounded p-3">
                <div>
                  <span className="text-[#FFF7ED] text-sm">
                    {item.quantity}x {item.name}
                  </span>
                  {item.notes && (
                    <p className="text-[#7C5C3E] text-xs mt-0.5">{item.notes}</p>
                  )}
                </div>
                <span className="font-mono text-[#FBBF24] text-sm">
                  {formatCents(item.total_cents)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Totals */}
        <div className="border-t border-[#3D2B1A] pt-3 space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-[#7C5C3E]">Subtotal</span>
            <span className="font-mono text-[#FFF7ED]">{formatCents(order.subtotal_cents)}</span>
          </div>
          {order.delivery_fee_cents > 0 && (
            <div className="flex justify-between text-sm">
              <span className="text-[#7C5C3E]">Taxa de entrega</span>
              <span className="font-mono text-[#FFF7ED]">{formatCents(order.delivery_fee_cents)}</span>
            </div>
          )}
          <div className="flex justify-between font-bold pt-1">
            <span className="text-[#D6B896]">Total</span>
            <span className="font-mono text-[#FBBF24] text-lg">{formatCents(order.total_cents)}</span>
          </div>
        </div>

        {/* Back button */}
        <button
          onClick={() => router.push("/")}
          className="w-full bg-[#251A0E] border border-[#3D2B1A] text-[#D6B896] font-semibold py-3 rounded text-sm hover:border-[#F97316] transition-colors"
        >
          Voltar ao cardapio
        </button>
      </div>
    </div>
  );
}
