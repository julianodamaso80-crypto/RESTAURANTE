"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import {
  ShoppingCart,
  ChefHat,
  Store,
  LayoutDashboard,
  Package,
  Users,
  Megaphone,
  Plug,
  LogOut,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/operator", icon: ShoppingCart, label: "Pedidos" },
  { href: "/kds", icon: ChefHat, label: "Cozinha" },
  { href: "/menu", icon: Store, label: "Cardápio" },
  { href: "/admin", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/stock", icon: Package, label: "Estoque" },
  { href: "/customers", icon: Users, label: "Clientes" },
  { href: "/crm", icon: Megaphone, label: "CRM" },
  { href: "/integracoes", icon: Plug, label: "Integrações" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <aside className="fixed left-0 top-0 h-screen w-14 bg-surface border-r border-border flex flex-col items-center py-3 z-50">
      {/* Logo */}
      <Link
        href="/operator"
        className="w-9 h-9 rounded-md overflow-hidden mb-6"
      >
        <img src="/assets/images/logo.png" alt="MesaMestre" width={36} height={36} />
      </Link>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col items-center gap-1 w-full">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              className={cn(
                "relative w-full flex items-center justify-center h-10 transition-colors group",
                isActive
                  ? "bg-accent/10 text-accent"
                  : "text-muted hover:text-foreground hover:bg-surface-2"
              )}
            >
              {isActive && (
                <div className="absolute left-0 top-1 bottom-1 w-0.5 bg-accent rounded-r" />
              )}
              <item.icon className="w-5 h-5" />
              {/* Tooltip */}
              <span className="absolute left-14 bg-surface-2 border border-border text-foreground text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap transition-opacity z-50">
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <button
        onClick={logout}
        title="Sair"
        className="w-full flex items-center justify-center h-10 text-muted hover:text-danger transition-colors"
      >
        <LogOut className="w-5 h-5" />
      </button>
    </aside>
  );
}
