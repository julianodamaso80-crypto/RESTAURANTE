"use client";

import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "primary" | "accent";

const VARIANT_STYLES: Record<BadgeVariant, string> = {
  default: "bg-surface-2 text-foreground-secondary",
  success: "bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-400 ring-1 ring-inset ring-amber-500/20",
  danger: "bg-red-500/10 text-red-400 ring-1 ring-inset ring-red-500/20",
  info: "bg-blue-500/10 text-blue-400 ring-1 ring-inset ring-blue-500/20",
  primary: "bg-primary/10 text-primary ring-1 ring-inset ring-primary/20",
  accent: "bg-accent/10 text-accent ring-1 ring-inset ring-accent/20",
};

interface BadgeProps {
  variant?: BadgeVariant;
  dot?: boolean;
  children: ReactNode;
  className?: string;
}

export function Badge({ variant = "default", dot = false, children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-medium rounded-full",
        VARIANT_STYLES[variant],
        className
      )}
    >
      {dot && (
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      )}
      {children}
    </span>
  );
}
