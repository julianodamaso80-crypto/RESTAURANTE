"use client";

import { useParams } from "next/navigation";
import { useKDSStations, useKDSTickets } from "@/hooks/useKDS";
import { KDSColumn } from "@/components/kds/KDSColumn";
import { Header } from "@/components/layout/Header";
import { RefreshCw, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function KDSStationPage() {
  const { stationId } = useParams<{ stationId: string }>();
  const { stations } = useKDSStations();
  const { tickets, loading, refresh } = useKDSTickets(stationId);

  const station = stations.find((s) => s.id === stationId);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-muted text-sm animate-pulse">
          Carregando estação...
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
      <Header title="Cozinha" subtitle={station?.name} />

      {/* Status bar */}
      <div className="flex items-center gap-4 px-4 py-2.5 border-b border-border bg-background-secondary">
        <Link
          href="/kds"
          className="flex items-center gap-1 text-muted hover:text-foreground transition-colors text-xs font-semibold"
        >
          <ArrowLeft size={12} /> Todas estações
        </Link>
        <span className="text-border">|</span>
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

      {/* Single station full-width */}
      <div className="flex-1 overflow-y-auto p-4">
        {station ? (
          <div className="max-w-md mx-auto">
            <KDSColumn station={station} tickets={tickets} onUpdate={refresh} />
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted text-sm">
              Estação não encontrada
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
