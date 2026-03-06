"use client";

import { cn } from "@/lib/utils";
import type { ReactNode, ThHTMLAttributes, TdHTMLAttributes, HTMLAttributes } from "react";

export function Table({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className="overflow-x-auto">
      <table className={cn("w-full text-sm", className)}>{children}</table>
    </div>
  );
}

export function TableHeader({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <thead className={cn("", className)}>
      {children}
    </thead>
  );
}

export function TableRow({ children, className, hover = false, ...props }: HTMLAttributes<HTMLTableRowElement> & { hover?: boolean }) {
  return (
    <tr
      className={cn(
        "border-b border-border/60",
        hover && "hover:bg-surface/40 transition-colors cursor-pointer",
        className
      )}
      {...props}
    >
      {children}
    </tr>
  );
}

export function TableHead({ children, className, ...props }: ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={cn(
        "px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider bg-background-secondary/50",
        className
      )}
      {...props}
    >
      {children}
    </th>
  );
}

export function TableCell({ children, className, ...props }: TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={cn("px-4 py-3.5 text-foreground-secondary", className)} {...props}>
      {children}
    </td>
  );
}

export function TableBody({ children, className }: { children: ReactNode; className?: string }) {
  return <tbody className={cn("divide-y divide-border/40", className)}>{children}</tbody>;
}
