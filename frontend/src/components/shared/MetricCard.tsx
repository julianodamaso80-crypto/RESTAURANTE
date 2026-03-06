"use client";

import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

const ACCENT_STYLES = {
  default: { bg: "bg-primary/10", text: "text-primary", ring: "ring-primary/20" },
  green: { bg: "bg-emerald-500/10", text: "text-emerald-400", ring: "ring-emerald-500/20" },
  yellow: { bg: "bg-amber-500/10", text: "text-amber-400", ring: "ring-amber-500/20" },
  red: { bg: "bg-red-500/10", text: "text-red-400", ring: "ring-red-500/20" },
  blue: { bg: "bg-blue-500/10", text: "text-blue-400", ring: "ring-blue-500/20" },
} as const;

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  accent?: keyof typeof ACCENT_STYLES;
  className?: string;
}

export function MetricCard({ label, value, icon: Icon, trend, accent = "default", className }: MetricCardProps) {
  const style = ACCENT_STYLES[accent];

  return (
    <div
      className={cn(
        "bg-background-secondary border border-border rounded-lg p-4 flex items-start gap-4 shadow-card",
        className
      )}
    >
      <div className={cn("p-2.5 rounded-lg ring-1 ring-inset", style.bg, style.ring)}>
        <Icon className={cn("w-5 h-5", style.text)} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-muted uppercase tracking-wider">{label}</p>
        <p className="text-2xl font-semibold text-foreground mt-1 tabular-nums">
          {value}
        </p>
        {trend && (
          <p className="text-xs text-muted-light mt-1">{trend}</p>
        )}
      </div>
    </div>
  );
}
