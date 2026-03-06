"use client";

import { useKDSStations, useKDSTickets } from "@/hooks/useKDS";
import { KDSBoard } from "@/components/kds/KDSBoard";
import { Header } from "@/components/layout/Header";
import { RefreshCw } from "lucide-react";

export default function KDSPage() {
  const { stations, loading: loadingStations } = useKDSStations();
  const { tickets, loading: loadingTickets, refresh } = useKDSTickets();

  if (loadingStations || loadingTickets) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-muted text-sm animate-pulse">
          Carregando cozinha...
        </div>
      </div>
    );
  }

  const inProgressCount = tickets.filter(
    (t) => t.status === "IN_PROGRESS",
  ).length;
  const waitingCount = tickets.filter((t) => t.status === "WAITING").length;

  return (
    <div className="flex flex-col h-full">
      <Header title="Cozinha" subtitle="KDS" />

      {/* Status bar */}
      <div className="flex items-center gap-4 px-4 py-2.5 border-b border-border bg-background-secondary">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
          <span className="text-xs text-muted">
            Polling a cada 5s
          </span>
        </div>
        <span className="text-border">|</span>
        <span className="text-xs text-muted tabular-nums">
          {inProgressCount} em preparo &middot; {waitingCount} na fila
        </span>
        <button
          onClick={() => refresh()}
          className="ml-auto text-muted hover:text-foreground transition-colors"
          title="Atualizar agora"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {/* Board */}
      <KDSBoard
        stations={stations}
        tickets={tickets}
        onUpdate={refresh}
      />
    </div>
  );
}
