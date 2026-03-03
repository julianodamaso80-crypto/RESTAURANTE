"use client";

import useSWR from "swr";
import api from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/shared/MetricCard";
import { StockAlertList } from "@/components/admin/StockAlertList";
import { TopCustomers } from "@/components/admin/TopCustomers";
import { RecentOrders } from "@/components/admin/RecentOrders";
import { CampaignStatus } from "@/components/admin/CampaignStatus";
import { QuotaBar } from "@/components/admin/QuotaBar";
import { ShoppingCart, Users, Package, RefreshCw } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { Order, PaginatedResponse } from "@/types/api";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

export default function AdminDashboard() {
  const { data: ordersData, mutate } = useSWR<PaginatedResponse<Order>>(
    "/orders/?status=DELIVERED&ordering=-delivered_at&page_size=100",
    fetcher
  );
  const { data: customersData } = useSWR<PaginatedResponse<unknown>>(
    "/customers/?page_size=1",
    fetcher
  );
  const { data: alertsData } = useSWR<PaginatedResponse<unknown>>(
    "/stock/alerts/?open=true&page_size=1",
    fetcher
  );

  const todayRevenue = (ordersData?.results ?? []).reduce(
    (s, o) => s + parseFloat(o.total || "0"),
    0
  );
  const totalOrders = ordersData?.count ?? 0;
  const totalCustomers = customersData?.count ?? 0;
  const openAlerts = alertsData?.count ?? 0;

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <Header title="Dashboard // Gestão" />

      {/* Métricas principais */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 p-4 border-b border-border">
        <MetricCard
          label="Receita hoje"
          value={formatCurrency(todayRevenue)}
          icon={ShoppingCart}
          accent="green"
        />
        <MetricCard
          label="Pedidos entregues"
          value={totalOrders}
          icon={ShoppingCart}
        />
        <MetricCard label="Clientes" value={totalCustomers} icon={Users} />
        <MetricCard
          label="Alertas estoque"
          value={openAlerts}
          icon={Package}
          accent={openAlerts > 0 ? "yellow" : "default"}
        />
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border">
        <span className="text-muted text-xs font-mono">Dados do dia</span>
        <button
          onClick={() => mutate()}
          className="text-muted hover:text-foreground transition-colors"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {/* Grid de widgets */}
      <div className="p-4 grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        <RecentOrders />
        <StockAlertList />
        <TopCustomers />
        <CampaignStatus />
        <QuotaBar />
      </div>
    </div>
  );
}
