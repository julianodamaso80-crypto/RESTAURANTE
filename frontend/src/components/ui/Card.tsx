"use client";

import { cn } from "@/lib/utils";
import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  hover?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

const PADDING_STYLES = {
  none: "",
  sm: "p-4",
  md: "p-5",
  lg: "p-6",
};

export function Card({ children, hover = false, padding = "md", className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "bg-background-secondary rounded-lg border border-border shadow-card",
        PADDING_STYLES[padding],
        hover && "transition-all duration-200 hover:border-border-light hover:shadow-elevation-2 cursor-pointer",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-center justify-between mb-4", className)}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <h3 className={cn("text-sm font-semibold text-foreground", className)}>
      {children}
    </h3>
  );
}
