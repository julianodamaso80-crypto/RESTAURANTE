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
import { Button } from "@/components/ui/Button";
import { ShoppingCart, Users, Package, RefreshCw, TrendingUp } from "lucide-react";
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
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        title="Dashboard"
        subtitle="Visao geral do seu negocio"
        actions={
          <Button variant="ghost" size="sm" onClick={() => mutate()} icon={<RefreshCw className="w-3.5 h-3.5" />}>
            Atualizar
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto">
        {/* Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 p-6">
          <MetricCard
            label="Receita hoje"
            value={formatCurrency(todayRevenue)}
            icon={TrendingUp}
            accent="green"
          />
          <MetricCard
            label="Pedidos entregues"
            value={totalOrders}
            icon={ShoppingCart}
          />
          <MetricCard label="Clientes" value={totalCustomers} icon={Users} accent="blue" />
          <MetricCard
            label="Alertas estoque"
            value={openAlerts}
            icon={Package}
            accent={openAlerts > 0 ? "yellow" : "default"}
          />
        </div>

        {/* Widgets */}
        <div className="px-6 pb-6 grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          <RecentOrders />
          <StockAlertList />
          <TopCustomers />
          <CampaignStatus />
          <QuotaBar />
        </div>
      </div>
    </div>
  );
}
