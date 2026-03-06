"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/shared/MetricCard";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { formatCurrency, timeAgo } from "@/lib/utils";
import api from "@/lib/api";
import {
  Users,
  UserCheck,
  UserX,
  Crown,
  RefreshCw,
  X,
  ShieldCheck,
  ShieldOff,
} from "lucide-react";
import type { Customer, ConsentRecord, CustomerEvent, PaginatedResponse } from "@/types/api";

type RFVFilter = "all" | "vip" | "active" | "inactive";

function getRFVBadge(customer: Customer): { label: string; className: string } {
  const freq = customer.rfv_frequency ?? 0;
  const monetary = customer.rfv_monetary_cents ?? 0;
  const recency = customer.rfv_recency_days ?? 999;

  if (freq >= 10 && monetary >= 50000 && recency <= 30)
    return { label: "VIP", className: "bg-amber-500/15 text-amber-500 border-amber-500/30" };
  if (recency <= 30)
    return { label: "Ativo", className: "bg-green-500/15 text-green-500 border-green-500/30" };
  if (recency <= 90)
    return { label: "Regular", className: "bg-blue-500/15 text-blue-500 border-blue-500/30" };
  return { label: "Inativo", className: "bg-red-500/15 text-red-500 border-red-500/30" };
}

function getRFVCategory(customer: Customer): RFVFilter {
  const freq = customer.rfv_frequency ?? 0;
  const monetary = customer.rfv_monetary_cents ?? 0;
  const recency = customer.rfv_recency_days ?? 999;

  if (freq >= 10 && monetary >= 50000 && recency <= 30) return "vip";
  if (recency <= 30) return "active";
  if (recency > 90) return "inactive";
  return "active";
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<RFVFilter>("all");
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [drawerConsents, setDrawerConsents] = useState<ConsentRecord[]>([]);
  const [drawerEvents, setDrawerEvents] = useState<CustomerEvent[]>([]);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await api.get<Customer[] | PaginatedResponse<Customer>>("/customers/");
      const data = Array.isArray(res.data) ? res.data : res.data.results;
      setCustomers(data);
    } catch {
      setCustomers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(t);
    }
  }, [toast]);

  async function openDrawer(customer: Customer) {
    setSelectedCustomer(customer);
    setDrawerLoading(true);
    try {
      const [consentsRes, eventsRes] = await Promise.all([
        api.get<ConsentRecord[]>(`/customers/${customer.id}/consents/`),
        api.get<CustomerEvent[]>(`/customers/${customer.id}/events/`),
      ]);
      setDrawerConsents(Array.isArray(consentsRes.data) ? consentsRes.data : []);
      setDrawerEvents(Array.isArray(eventsRes.data) ? eventsRes.data : []);
    } catch {
      setDrawerConsents([]);
      setDrawerEvents([]);
    } finally {
      setDrawerLoading(false);
    }
  }

  const filteredCustomers = customers.filter((c) => {
    if (filter === "all") return true;
    return getRFVCategory(c) === filter;
  });

  const totalCustomers = customers.length;
  const activeCount = customers.filter((c) => (c.rfv_recency_days ?? 999) <= 30).length;
  const inactiveCount = customers.filter((c) => (c.rfv_recency_days ?? 999) > 90).length;
  const vipCount = customers.filter((c) => getRFVCategory(c) === "vip").length;

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <Header title="Clientes // CDP" />

      {/* Toast */}
      {toast && (
        <div
          className={`mx-4 mt-3 px-4 py-3 rounded-lg text-sm flex items-center gap-2 ${
            toast.type === "success"
              ? "bg-success/10 border border-success/20 text-success"
              : "bg-danger/10 border border-danger/20 text-danger"
          }`}
        >
          {toast.msg}
        </div>
      )}

      {/* Metricas */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 p-4 border-b border-border">
        <MetricCard label="Total clientes" value={totalCustomers} icon={Users} />
        <MetricCard
          label="Ativos (30d)"
          value={activeCount}
          icon={UserCheck}
          accent="green"
        />
        <MetricCard
          label="Inativos (90d+)"
          value={inactiveCount}
          icon={UserX}
          accent={inactiveCount > 0 ? "red" : "default"}
        />
        <MetricCard label="VIP" value={vipCount} icon={Crown} accent="yellow" />
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border">
        <div className="flex items-center gap-2">
          {(["all", "vip", "active", "inactive"] as RFVFilter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs font-mono px-3 py-1 rounded border transition-colors ${
                filter === f
                  ? "bg-accent/10 text-accent border-accent/30"
                  : "text-muted border-border hover:text-foreground hover:border-border-light"
              }`}
            >
              {f === "all" ? "Todos" : f === "vip" ? "VIP" : f === "active" ? "Ativos" : "Inativos"}
            </button>
          ))}
        </div>
        <button
          onClick={() => { setLoading(true); fetchData(); }}
          className="text-muted hover:text-foreground transition-colors"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {/* Tabela */}
      {loading ? (
        <div className="flex items-center justify-center p-12">
          <LoadingSpinner size="md" />
        </div>
      ) : filteredCustomers.length === 0 ? (
        <EmptyState
          icon={Users}
          title="Nenhum cliente encontrado"
          description={filter !== "all" ? "Nenhum cliente nesse segmento" : "Clientes aparecem automaticamente ao receber pedidos"}
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-muted text-xs font-mono uppercase tracking-wider">
                <th className="text-left px-4 py-3">Nome</th>
                <th className="text-left px-4 py-3">Telefone</th>
                <th className="text-left px-4 py-3">E-mail</th>
                <th className="text-right px-4 py-3">Pedidos</th>
                <th className="text-right px-4 py-3">Ticket medio</th>
                <th className="text-center px-4 py-3">RFV</th>
                <th className="text-right px-4 py-3">Ultima visita</th>
              </tr>
            </thead>
            <tbody>
              {filteredCustomers.map((customer) => {
                const badge = getRFVBadge(customer);
                const freq = customer.rfv_frequency ?? 0;
                const monetary = customer.rfv_monetary_cents ?? 0;
                const avgTicket = freq > 0 ? monetary / freq / 100 : 0;
                return (
                  <tr
                    key={customer.id}
                    onClick={() => openDrawer(customer)}
                    className="border-b border-border/50 hover:bg-surface-2/50 transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-3 text-foreground font-medium">
                      {customer.name || "Anonimo"}
                    </td>
                    <td className="px-4 py-3 text-muted font-mono text-xs">
                      {customer.phone || "—"}
                    </td>
                    <td className="px-4 py-3 text-muted text-xs">
                      {customer.email || "—"}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-foreground">
                      {freq}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-foreground">
                      {formatCurrency(avgTicket)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 text-xs font-mono font-medium rounded border ${badge.className}`}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-muted text-xs font-mono">
                      {customer.rfv_last_order_at
                        ? timeAgo(customer.rfv_last_order_at)
                        : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Drawer de detalhe */}
      {selectedCustomer && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setSelectedCustomer(null)}
          />
          <div className="relative w-full max-w-md bg-surface border-l border-border h-full overflow-y-auto">
            <div className="sticky top-0 bg-surface border-b border-border p-4 flex items-center justify-between z-10">
              <h2 className="text-foreground font-semibold">
                {selectedCustomer.name || "Anonimo"}
              </h2>
              <button
                onClick={() => setSelectedCustomer(null)}
                className="text-muted hover:text-foreground"
              >
                <X size={20} />
              </button>
            </div>

            {drawerLoading ? (
              <div className="flex items-center justify-center p-12">
                <LoadingSpinner size="md" />
              </div>
            ) : (
              <div className="p-4 space-y-6">
                {/* Info basica */}
                <div className="space-y-2">
                  <h3 className="text-muted text-xs font-mono uppercase tracking-wider">
                    Informacoes
                  </h3>
                  <div className="bg-surface-2 rounded-lg p-3 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted">Telefone</span>
                      <span className="text-foreground font-mono">
                        {selectedCustomer.phone || "—"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted">E-mail</span>
                      <span className="text-foreground">
                        {selectedCustomer.email || "—"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted">Desde</span>
                      <span className="text-foreground font-mono">
                        {new Intl.DateTimeFormat("pt-BR").format(
                          new Date(selectedCustomer.created_at)
                        )}
                      </span>
                    </div>
                  </div>
                </div>

                {/* RFV Score */}
                <div className="space-y-2">
                  <h3 className="text-muted text-xs font-mono uppercase tracking-wider">
                    Score RFV
                  </h3>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-surface-2 rounded-lg p-3 text-center">
                      <p className="text-xs text-muted">Recencia</p>
                      <p className="text-lg font-mono font-bold text-foreground">
                        {selectedCustomer.rfv_recency_days ?? "—"}
                      </p>
                      <p className="text-xs text-muted">dias</p>
                    </div>
                    <div className="bg-surface-2 rounded-lg p-3 text-center">
                      <p className="text-xs text-muted">Frequencia</p>
                      <p className="text-lg font-mono font-bold text-foreground">
                        {selectedCustomer.rfv_frequency ?? "—"}
                      </p>
                      <p className="text-xs text-muted">pedidos</p>
                    </div>
                    <div className="bg-surface-2 rounded-lg p-3 text-center">
                      <p className="text-xs text-muted">Monetario</p>
                      <p className="text-lg font-mono font-bold text-foreground">
                        {selectedCustomer.rfv_monetary_cents != null
                          ? formatCurrency(selectedCustomer.rfv_monetary_cents / 100)
                          : "—"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Consentimentos LGPD */}
                <div className="space-y-2">
                  <h3 className="text-muted text-xs font-mono uppercase tracking-wider">
                    Consentimentos LGPD
                  </h3>
                  <div className="bg-surface-2 rounded-lg p-3 space-y-2">
                    {selectedCustomer.consent_summary &&
                    Object.keys(selectedCustomer.consent_summary).length > 0 ? (
                      Object.entries(selectedCustomer.consent_summary).map(
                        ([channel, granted]) => (
                          <div
                            key={channel}
                            className="flex items-center justify-between text-sm"
                          >
                            <span className="text-muted font-mono text-xs uppercase">
                              {channel}
                            </span>
                            <span
                              className={`flex items-center gap-1 text-xs font-mono ${
                                granted ? "text-success" : "text-danger"
                              }`}
                            >
                              {granted ? (
                                <ShieldCheck size={12} />
                              ) : (
                                <ShieldOff size={12} />
                              )}
                              {granted ? "Concedido" : "Revogado"}
                            </span>
                          </div>
                        )
                      )
                    ) : (
                      <p className="text-muted text-xs font-mono">
                        Nenhum consentimento registrado
                      </p>
                    )}
                  </div>
                </div>

                {/* Historico de consentimentos */}
                {drawerConsents.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-muted text-xs font-mono uppercase tracking-wider">
                      Historico de consentimentos
                    </h3>
                    <div className="space-y-1 max-h-40 overflow-y-auto">
                      {drawerConsents.slice(0, 10).map((c) => (
                        <div
                          key={c.id}
                          className="flex items-center justify-between text-xs bg-surface-2 rounded px-3 py-2"
                        >
                          <span className="text-muted font-mono">{c.channel}</span>
                          <span
                            className={
                              c.status === "GRANTED"
                                ? "text-success font-mono"
                                : "text-danger font-mono"
                            }
                          >
                            {c.status === "GRANTED" ? "Concedido" : "Revogado"}
                          </span>
                          <span className="text-muted font-mono">
                            {new Intl.DateTimeFormat("pt-BR", {
                              day: "2-digit",
                              month: "2-digit",
                              hour: "2-digit",
                              minute: "2-digit",
                            }).format(new Date(c.created_at))}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Eventos recentes */}
                <div className="space-y-2">
                  <h3 className="text-muted text-xs font-mono uppercase tracking-wider">
                    Eventos recentes
                  </h3>
                  {drawerEvents.length === 0 ? (
                    <p className="text-muted text-xs font-mono">Nenhum evento</p>
                  ) : (
                    <div className="space-y-1 max-h-60 overflow-y-auto">
                      {drawerEvents.slice(0, 15).map((ev) => (
                        <div
                          key={ev.id}
                          className="flex items-center justify-between text-xs bg-surface-2 rounded px-3 py-2"
                        >
                          <span className="text-foreground font-mono">
                            {ev.event_type.replace(/_/g, " ")}
                          </span>
                          <span className="text-muted font-mono">
                            {timeAgo(ev.occurred_at)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
