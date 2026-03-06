"use client";

import { KDSColumn } from "./KDSColumn";
import type { KDSStation, KDSTicket } from "@/types/api";

interface KDSBoardProps {
  stations: KDSStation[];
  tickets: KDSTicket[];
  onUpdate: () => void;
}

export function KDSBoard({ stations, tickets, onUpdate }: KDSBoardProps) {
  return (
    <div className="flex-1 overflow-x-auto p-4">
      <div
        className="flex gap-4 h-full"
        style={{ minWidth: "max-content" }}
      >
        {stations.map((station) => (
          <KDSColumn
            key={station.id}
            station={station}
            tickets={tickets.filter((t) => t.station === station.id)}
            onUpdate={onUpdate}
          />
        ))}
        {stations.length === 0 && (
          <div className="flex items-center justify-center w-full">
            <p className="text-muted text-sm">
              Nenhuma estação configurada
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
