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
    <div className="bg-background-secondary border border-border rounded-lg shadow-card p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-muted uppercase tracking-wider">
          Quota CRM
        </span>
        <span className={`text-xs font-semibold tabular-nums ${textColor}`}>
          {data.current_period_contacts}/{data.max_contacts}
        </span>
      </div>
      <div className="w-full h-1.5 bg-surface/50 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {data.is_blocked && (
        <p className="text-danger text-xs mt-2">
          Quota esgotada — disparos bloqueados
        </p>
      )}
    </div>
  );
}
