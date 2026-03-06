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
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useState, useEffect, createContext, useContext } from "react";

const SidebarContext = createContext(false);
export const useSidebarCollapsed = () => useContext(SidebarContext);

const NAV_SECTIONS = [
  {
    label: "Operacional",
    items: [
      { href: "/operator", icon: ShoppingCart, label: "Pedidos" },
      { href: "/kds", icon: ChefHat, label: "Cozinha" },
      { href: "/menu", icon: Store, label: "Cardapio" },
    ],
  },
  {
    label: "Gestao",
    items: [
      { href: "/admin", icon: LayoutDashboard, label: "Dashboard" },
      { href: "/stock", icon: Package, label: "Estoque" },
      { href: "/customers", icon: Users, label: "Clientes" },
      { href: "/crm", icon: Megaphone, label: "CRM" },
    ],
  },
  {
    label: "Configuracoes",
    items: [
      { href: "/integracoes", icon: Plug, label: "Integracoes" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 1024px)");
    const handler = (e: MediaQueryListEvent | MediaQueryList) => {
      if (e.matches) setCollapsed(true);
    };
    handler(mq);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  return (
    <SidebarContext.Provider value={collapsed}>
      <aside
        data-collapsed={collapsed}
        className={cn(
          "fixed left-0 top-0 h-screen bg-background-secondary border-r border-border flex flex-col z-50 transition-all duration-300",
          collapsed ? "w-16" : "w-60"
        )}
      >
        {/* Logo */}
        <div className={cn("flex items-center h-16 border-b border-border shrink-0", collapsed ? "justify-center px-2" : "px-4 gap-3")}>
          <Link href="/operator" className="w-9 h-9 rounded-lg overflow-hidden shrink-0">
            <img src="/assets/images/logo.png" alt="MesaMestre" width={36} height={36} />
          </Link>
          {!collapsed && (
            <span className="text-sm font-semibold text-foreground">MesaMestre</span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-6">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label}>
              {!collapsed && (
                <p className="px-3 mb-2 text-[10px] font-semibold text-muted uppercase tracking-widest">
                  {section.label}
                </p>
              )}
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const isActive = pathname.startsWith(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      title={collapsed ? item.label : undefined}
                      className={cn(
                        "relative flex items-center gap-3 rounded-lg transition-all duration-200 group",
                        collapsed ? "justify-center h-10 w-full" : "h-10 px-3",
                        isActive
                          ? "bg-primary/10 text-primary font-medium"
                          : "text-muted-light hover:text-foreground hover:bg-surface/50"
                      )}
                    >
                      {isActive && (
                        <div className="absolute left-0 top-2 bottom-2 w-[3px] bg-primary rounded-r-full" />
                      )}
                      <item.icon className="w-[18px] h-[18px] shrink-0" />
                      {!collapsed && (
                        <span className="text-sm truncate">{item.label}</span>
                      )}
                      {collapsed && (
                        <span className="absolute left-full ml-2 bg-surface-2 text-foreground text-xs px-2.5 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap transition-opacity shadow-elevation-2 z-50">
                          {item.label}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t border-border p-2 space-y-0.5">
          <button
            onClick={logout}
            title="Sair"
            className={cn(
              "flex items-center gap-3 w-full rounded-lg text-muted-light hover:text-red-400 hover:bg-red-500/10 transition-all duration-200",
              collapsed ? "justify-center h-10" : "h-10 px-3"
            )}
          >
            <LogOut className="w-[18px] h-[18px] shrink-0" />
            {!collapsed && <span className="text-sm">Sair</span>}
          </button>

          <button
            onClick={() => setCollapsed(!collapsed)}
            className={cn(
              "flex items-center gap-3 w-full rounded-lg text-muted hover:text-foreground hover:bg-surface/50 transition-all duration-200",
              collapsed ? "justify-center h-10" : "h-10 px-3"
            )}
          >
            {collapsed ? (
              <ChevronRight className="w-[18px] h-[18px]" />
            ) : (
              <>
                <ChevronLeft className="w-[18px] h-[18px]" />
                <span className="text-sm">Recolher</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </SidebarContext.Provider>
  );
}
