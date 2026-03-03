"use client";

import useSWR from "swr";
import api from "@/lib/api";
import { Megaphone } from "lucide-react";
import type { PaginatedResponse } from "@/types/api";

interface Campaign {
  id: string;
  name: string;
  status: string;
}

const STATUS_COLOR: Record<string, string> = {
  DRAFT: "text-muted",
  SCHEDULED: "text-blue-500",
  RUNNING: "text-warning",
  COMPLETED: "text-success",
  CANCELLED: "text-danger",
};

export function CampaignStatus() {
  const { data } = useSWR<PaginatedResponse<Campaign>>(
    "/crm/campaigns/?page_size=5",
    (url: string) => api.get(url).then((r) => r.data)
  );
  const campaigns = data?.results ?? [];

  return (
    <div className="bg-surface border border-border rounded p-4">
      <div className="flex items-center gap-2 mb-3">
        <Megaphone size={14} className="text-muted" />
        <h3 className="text-muted text-xs font-mono uppercase tracking-wider">
          Campanhas
        </h3>
      </div>
      <div className="space-y-2">
        {campaigns.map((campaign) => (
          <div key={campaign.id} className="flex items-center justify-between">
            <span className="text-foreground text-sm truncate">
              {campaign.name}
            </span>
            <span
              className={`font-mono text-xs ${STATUS_COLOR[campaign.status] ?? "text-muted"}`}
            >
              {campaign.status}
            </span>
          </div>
        ))}
        {campaigns.length === 0 && (
          <p className="text-muted text-xs font-mono">Sem campanhas</p>
        )}
      </div>
    </div>
  );
}
