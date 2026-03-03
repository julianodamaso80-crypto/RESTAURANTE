"use client";

import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

const ACCENT_STYLES = {
  default: { bg: "bg-accent/10", text: "text-accent" },
  green: { bg: "bg-success/10", text: "text-success" },
  yellow: { bg: "bg-warning/10", text: "text-warning" },
  red: { bg: "bg-danger/10", text: "text-danger" },
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
        "bg-surface border border-border rounded p-4 flex items-start gap-3",
        className
      )}
    >
      <div className={cn("p-2 rounded", style.bg)}>
        <Icon className={cn("w-5 h-5", style.text)} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-muted uppercase tracking-wider">{label}</p>
        <p className="text-2xl font-mono font-bold text-foreground mt-0.5">
          {value}
        </p>
        {trend && (
          <p className="text-xs text-muted mt-1">{trend}</p>
        )}
      </div>
    </div>
  );
}
