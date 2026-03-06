"use client";

import { KDSTicketCard } from "./KDSTicketCard";
import type { KDSStation, KDSTicket } from "@/types/api";

interface KDSColumnProps {
  station: KDSStation;
  tickets: KDSTicket[];
  onUpdate: () => void;
}

export function KDSColumn({ station, tickets, onUpdate }: KDSColumnProps) {
  const waiting = tickets.filter((t) => t.status === "WAITING");
  const inProgress = tickets.filter((t) => t.status === "IN_PROGRESS");

  return (
    <div className="flex flex-col min-w-[280px] max-w-[320px] bg-background-secondary border border-border rounded-lg overflow-hidden">
      {/* Station header */}
      <div className="px-3 py-2 border-b border-border flex items-center justify-between">
        <h2 className="font-semibold text-foreground text-sm uppercase tracking-wider">
          {station.name}
        </h2>
        <div className="flex items-center gap-2">
          {inProgress.length > 0 && (
            <span className="text-xs tabular-nums text-primary bg-primary/10 px-2 py-0.5 rounded-lg border border-primary/20">
              {inProgress.length} fazendo
            </span>
          )}
          {waiting.length > 0 && (
            <span className="text-xs tabular-nums text-muted bg-surface/50 px-2 py-0.5 rounded-lg">
              {waiting.length} fila
            </span>
          )}
        </div>
      </div>

      {/* IN_PROGRESS first, then WAITING */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {inProgress.map((ticket) => (
          <KDSTicketCard key={ticket.id} ticket={ticket} onUpdate={onUpdate} />
        ))}
        {waiting.map((ticket) => (
          <KDSTicketCard key={ticket.id} ticket={ticket} onUpdate={onUpdate} />
        ))}
        {tickets.length === 0 && (
          <div className="flex items-center justify-center h-24">
            <p className="text-muted text-xs">Sem pedidos</p>
          </div>
        )}
      </div>
    </div>
  );
}
