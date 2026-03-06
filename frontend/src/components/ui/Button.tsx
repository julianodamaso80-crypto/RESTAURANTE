"use client";

import { cn } from "@/lib/utils";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "accent" | "outline";
type Size = "sm" | "md" | "lg";

const VARIANT_STYLES: Record<Variant, string> = {
  primary:
    "bg-primary text-white hover:bg-primary-600 active:bg-primary-700 shadow-elevation-1 hover:shadow-glow",
  secondary:
    "bg-surface text-foreground hover:bg-surface-2 border border-border",
  ghost:
    "bg-transparent text-foreground-secondary hover:bg-surface hover:text-foreground",
  danger:
    "bg-danger text-white hover:bg-red-600 active:bg-red-700",
  accent:
    "bg-accent text-black hover:bg-accent-600 active:bg-accent-700 shadow-elevation-1 hover:shadow-glow-accent",
  outline:
    "bg-transparent border border-border-light text-foreground-secondary hover:bg-surface hover:text-foreground hover:border-primary/40",
};

const SIZE_STYLES: Record<Size, string> = {
  sm: "h-8 px-3 text-xs gap-1.5 rounded-sm",
  md: "h-10 px-4 text-sm gap-2 rounded",
  lg: "h-12 px-6 text-sm gap-2.5 rounded-lg",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
  children: ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium transition-all duration-200 focus-ring disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none",
        VARIANT_STYLES[variant],
        SIZE_STYLES[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <LoadingSpinner size="sm" />
      ) : (
        <>
          {icon && <span className="shrink-0">{icon}</span>}
          {children}
        </>
      )}
    </button>
  );
}
