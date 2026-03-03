"use client";

import useSWR from "swr";
import api from "@/lib/api";
import { AlertTriangle } from "lucide-react";
import type { PaginatedResponse } from "@/types/api";

interface StockAlert {
  id: string;
  stock_item_name: string;
  current_qty: number;
  minimum_qty: number;
  stock_item_unit: string;
}

export function StockAlertList() {
  const { data } = useSWR<PaginatedResponse<StockAlert>>(
    "/stock/alerts/?open=true",
    (url: string) => api.get(url).then((r) => r.data)
  );
  const alerts = data?.results ?? [];

  return (
    <div className="bg-surface border border-border rounded p-4">
      <div className="flex items-center gap-2 mb-3">
        <AlertTriangle
          size={14}
          className={alerts.length > 0 ? "text-warning" : "text-muted"}
        />
        <h3 className="text-muted text-xs font-mono uppercase tracking-wider">
          Estoque crítico
        </h3>
        {alerts.length > 0 && (
          <span className="ml-auto font-mono text-xs text-warning bg-warning/10 px-2 py-0.5 rounded border border-warning/20">
            {alerts.length}
          </span>
        )}
      </div>

      {alerts.length === 0 ? (
        <p className="text-muted text-xs font-mono">Nenhum alerta aberto</p>
      ) : (
        <div className="space-y-2">
          {alerts.slice(0, 5).map((alert) => (
            <div key={alert.id} className="flex items-center justify-between">
              <span className="text-foreground text-sm truncate">
                {alert.stock_item_name}
              </span>
              <span className="font-mono text-danger text-xs shrink-0 ml-2">
                {alert.current_qty} / {alert.minimum_qty}{" "}
                {alert.stock_item_unit}
              </span>
            </div>
          ))}
          {alerts.length > 5 && (
            <p className="text-muted text-xs font-mono">
              +{alerts.length - 5} mais
            </p>
          )}
        </div>
      )}
    </div>
  );
}
