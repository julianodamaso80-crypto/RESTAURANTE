"use client";

import useSWR from "swr";
import api from "@/lib/api";

interface QuotaData {
  current_period_contacts: number;
  max_contacts: number;
  is_blocked: boolean;
}

export function QuotaBar() {
  const { data } = useSWR<QuotaData>("/crm/billing/quota/", (url: string) =>
    api.get(url).then((r) => r.data)
  );
  if (!data) return null;

  const pct = Math.min(
    100,
    (data.current_period_contacts / data.max_contacts) * 100
  );
  const barColor =
    pct >= 100 ? "bg-danger" : pct >= 80 ? "bg-warning" : "bg-success";
  const textColor =
    pct >= 100
      ? "text-danger"
      : pct >= 80
        ? "text-warning"
        : "text-success";

  return (
    <div className="bg-surface border border-border rounded p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-muted text-xs font-mono uppercase tracking-wider">
          Quota CRM
        </span>
        <span className={`font-mono text-xs font-bold ${textColor}`}>
          {data.current_period_contacts}/{data.max_contacts}
        </span>
      </div>
      <div className="w-full h-1.5 bg-surface-2 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {data.is_blocked && (
        <p className="text-danger text-xs font-mono mt-2">
          Quota esgotada — disparos bloqueados
        </p>
      )}
    </div>
  );
}
