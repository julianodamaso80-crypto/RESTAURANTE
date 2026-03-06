"use client";

import { cn } from "@/lib/utils";
import { CheckCircle, AlertTriangle, XCircle, Info, X } from "lucide-react";
import type { ReactNode } from "react";

type ToastVariant = "success" | "error" | "warning" | "info";

const VARIANT_CONFIG: Record<ToastVariant, { icon: ReactNode; style: string }> = {
  success: {
    icon: <CheckCircle className="w-4 h-4" />,
    style: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
  },
  error: {
    icon: <XCircle className="w-4 h-4" />,
    style: "bg-red-500/10 border-red-500/20 text-red-400",
  },
  warning: {
    icon: <AlertTriangle className="w-4 h-4" />,
    style: "bg-amber-500/10 border-amber-500/20 text-amber-400",
  },
  info: {
    icon: <Info className="w-4 h-4" />,
    style: "bg-blue-500/10 border-blue-500/20 text-blue-400",
  },
};

interface ToastProps {
  variant: ToastVariant;
  message: string;
  onClose?: () => void;
  className?: string;
}

export function Toast({ variant, message, onClose, className }: ToastProps) {
  const config = VARIANT_CONFIG[variant];

  return (
    <div
      className={cn(
        "flex items-center gap-2.5 px-4 py-3 rounded-lg border text-sm animate-slide-in-up",
        config.style,
        className
      )}
    >
      <span className="shrink-0">{config.icon}</span>
      <span className="flex-1">{message}</span>
      {onClose && (
        <button onClick={onClose} className="shrink-0 opacity-60 hover:opacity-100 transition-opacity">
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
