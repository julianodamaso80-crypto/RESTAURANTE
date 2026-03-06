"use client";

import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useCallback } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  icon?: ReactNode;
  children: ReactNode;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const SIZE_STYLES = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
};

export function Modal({
  open,
  onClose,
  title,
  description,
  icon,
  children,
  size = "md",
  className,
}: ModalProps) {
  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (open) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [open, handleEscape]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div
        className={cn(
          "relative w-full mx-4 bg-background-secondary border border-border rounded-xl shadow-elevation-4 animate-scale-in",
          SIZE_STYLES[size],
          className
        )}
      >
        {/* Header */}
        <div className="flex items-start gap-3 p-6 pb-0">
          {icon && (
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              {icon}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-foreground">{title}</h3>
            {description && (
              <p className="text-sm text-muted mt-0.5">{description}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-muted hover:text-foreground hover:bg-surface transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}
