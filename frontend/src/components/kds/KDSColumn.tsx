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
    <div className="flex flex-col min-w-[280px] max-w-[320px] bg-surface border border-border rounded overflow-hidden">
      {/* Station header */}
      <div className="px-3 py-2 border-b border-border flex items-center justify-between">
        <h2 className="font-mono font-bold text-foreground text-sm uppercase tracking-wider">
          {station.name}
        </h2>
        <div className="flex items-center gap-2">
          {inProgress.length > 0 && (
            <span className="font-mono text-xs text-accent bg-accent/10 px-2 py-0.5 rounded border border-accent/20">
              {inProgress.length} fazendo
            </span>
          )}
          {waiting.length > 0 && (
            <span className="font-mono text-xs text-muted bg-surface-2 px-2 py-0.5 rounded">
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
            <p className="text-muted font-mono text-xs">Sem pedidos</p>
          </div>
        )}
      </div>
    </div>
  );
}
