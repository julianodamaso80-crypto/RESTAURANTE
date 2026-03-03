"use client";

import { useAuthStore } from "@/store/auth";

interface HeaderProps {
  title: string;
}

export function Header({ title }: HeaderProps) {
  const user = useAuthStore((s) => s.user);

  return (
    <header className="h-14 bg-surface border-b border-border flex items-center justify-between px-6">
      <h1 className="text-lg font-mono font-bold text-foreground">{title}</h1>

      <div className="flex items-center gap-3">
        <div className="text-right">
          <p className="text-sm text-foreground leading-tight">
            {user?.full_name || "Operador"}
          </p>
          <p className="text-xs text-muted leading-tight">
            {user?.role || "operator"}
          </p>
        </div>
        <div className="w-8 h-8 bg-accent/20 rounded flex items-center justify-center">
          <span className="text-xs font-mono font-bold text-accent">
            {(user?.full_name || "O")[0].toUpperCase()}
          </span>
        </div>
      </div>
    </header>
  );
}
