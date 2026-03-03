"use client";

import { useState } from "react";
import { ChevronRight, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { KDSTimer } from "./KDSTimer";
import { advanceTicketStatus } from "@/hooks/useKDS";
import type { KDSTicket } from "@/types/api";

interface KDSTicketCardProps {
  ticket: KDSTicket;
  onUpdate: () => void;
}

export function KDSTicketCard({ ticket, onUpdate }: KDSTicketCardProps) {
  const [loading, setLoading] = useState(false);

  const isWaiting = ticket.status === "WAITING";
  const isInProgress = ticket.status === "IN_PROGRESS";

  async function handleAdvance() {
    setLoading(true);
    try {
      const next = isWaiting ? "IN_PROGRESS" : "DONE";
      await advanceTicketStatus(ticket.id, next);
      onUpdate();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className={cn(
        "border rounded p-3 transition-all",
        isWaiting && "bg-surface border-border",
        isInProgress && "bg-accent/5 border-accent/30",
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "font-mono font-bold text-lg",
              isInProgress ? "text-accent" : "text-foreground",
            )}
          >
            {ticket.order_display_number}
          </span>
          {isInProgress && (
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          )}
        </div>
        <KDSTimer
          startTime={ticket.enqueued_at}
          warningAfterMinutes={10}
          criticalAfterMinutes={15}
        />
      </div>

      {/* Items */}
      <ul className="space-y-1 mb-3">
        {ticket.items?.map((item) => (
          <li key={item.id} className="flex items-baseline gap-2">
            <span className="font-mono font-bold text-accent text-sm w-5 text-right shrink-0">
              {item.quantity}x
            </span>
            <span className="text-foreground text-sm leading-tight">
              {item.name}
            </span>
          </li>
        ))}
      </ul>

      {/* Action */}
      <button
        onClick={handleAdvance}
        disabled={loading}
        className={cn(
          "w-full flex items-center justify-center gap-2 py-2 rounded font-mono text-xs uppercase tracking-wider font-bold transition-all",
          isWaiting &&
            "bg-warning/10 text-warning border border-warning/20 hover:bg-warning/20",
          isInProgress &&
            "bg-success/10 text-success border border-success/20 hover:bg-success/20",
          loading && "opacity-50",
        )}
      >
        {isWaiting ? (
          <>
            <ChevronRight size={14} /> Iniciar
          </>
        ) : (
          <>
            <Check size={14} /> Concluir
          </>
        )}
      </button>
    </div>
  );
}
