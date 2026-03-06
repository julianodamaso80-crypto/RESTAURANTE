"use client";

import { useAuthStore } from "@/store/auth";
import { Bell, Search } from "lucide-react";

interface HeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function Header({ title, subtitle, actions }: HeaderProps) {
  const user = useAuthStore((s) => s.user);

  const initials = (user?.full_name || "U")
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <header className="h-16 bg-background-secondary/80 backdrop-blur-md border-b border-border flex items-center justify-between px-6 shrink-0 sticky top-0 z-40">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-base font-semibold text-foreground leading-tight">{title}</h1>
          {subtitle && (
            <p className="text-xs text-muted mt-0.5">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {actions}

        <button className="w-9 h-9 flex items-center justify-center rounded-lg text-muted hover:text-foreground hover:bg-surface transition-colors">
          <Search className="w-4 h-4" />
        </button>

        <button className="relative w-9 h-9 flex items-center justify-center rounded-lg text-muted hover:text-foreground hover:bg-surface transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary rounded-full" />
        </button>

        <div className="h-6 w-px bg-border mx-1" />

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-foreground leading-tight">
              {user?.full_name || "Operador"}
            </p>
            <p className="text-xs text-muted leading-tight capitalize">
              {user?.role || "operator"}
            </p>
          </div>
          <div className="w-9 h-9 bg-primary/15 rounded-lg flex items-center justify-center ring-1 ring-inset ring-primary/20">
            <span className="text-xs font-semibold text-primary">
              {initials}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
