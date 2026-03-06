"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/shared/MetricCard";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Toast } from "@/components/ui/Toast";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/Table";
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

function getRFVBadge(customer: Customer): { label: string; variant: "accent" | "success" | "info" | "danger" } {
  const freq = customer.rfv_frequency ?? 0;
  const monetary = customer.rfv_monetary_cents ?? 0;
  const recency = customer.rfv_recency_days ?? 999;
  if (freq >= 10 && monetary >= 50000 && recency <= 30) return { label: "VIP", variant: "accent" };
  if (recency <= 30) return { label: "Ativo", variant: "success" };
  if (recency <= 90) return { label: "Regular", variant: "info" };
  return { label: "Inativo", variant: "danger" };
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

  useEffect(() => { fetchData(); }, [fetchData]);

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
  const filters: { key: RFVFilter; label: string }[] = [
    { key: "all", label: "Todos" },
    { key: "vip", label: "VIP" },
    { key: "active", label: "Ativos" },
    { key: "inactive", label: "Inativos" },
  ];

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        title="Clientes"
        subtitle="Customer Data Platform"
        actions={
          <Button variant="ghost" size="sm" onClick={() => { setLoading(true); fetchData(); }} icon={<RefreshCw className="w-3.5 h-3.5" />}>
            Atualizar
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto">
        {toast && (
          <div className="px-6 pt-4">
            <Toast variant={toast.type === "success" ? "success" : "error"} message={toast.msg} onClose={() => setToast(null)} />
          </div>
        )}

        {/* Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 p-6">
          <MetricCard label="Total clientes" value={totalCustomers} icon={Users} />
          <MetricCard label="Ativos (30d)" value={activeCount} icon={UserCheck} accent="green" />
          <MetricCard label="Inativos (90d+)" value={inactiveCount} icon={UserX} accent={inactiveCount > 0 ? "red" : "default"} />
          <MetricCard label="VIP" value={vipCount} icon={Crown} accent="yellow" />
        </div>

        {/* Filters */}
        <div className="px-6 pb-4 flex items-center gap-2">
          {filters.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`text-sm px-3.5 py-1.5 rounded-lg border transition-all duration-200 ${
                filter === f.key
                  ? "bg-primary/10 text-primary border-primary/20 font-medium"
                  : "text-muted border-border hover:text-foreground hover:border-border-light"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Table */}
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
          <div className="px-6 pb-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Telefone</TableHead>
                  <TableHead>E-mail</TableHead>
                  <TableHead className="text-right">Pedidos</TableHead>
                  <TableHead className="text-right">Ticket medio</TableHead>
                  <TableHead className="text-center">RFV</TableHead>
                  <TableHead className="text-right">Ultima visita</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCustomers.map((customer) => {
                  const badge = getRFVBadge(customer);
                  const freq = customer.rfv_frequency ?? 0;
                  const monetary = customer.rfv_monetary_cents ?? 0;
                  const avgTicket = freq > 0 ? monetary / freq / 100 : 0;
                  return (
                    <TableRow key={customer.id} hover onClick={() => openDrawer(customer)}>
                      <TableCell className="font-medium text-foreground">{customer.name || "Anonimo"}</TableCell>
                      <TableCell className="text-muted text-xs">{customer.phone || "\u2014"}</TableCell>
                      <TableCell className="text-muted text-xs">{customer.email || "\u2014"}</TableCell>
                      <TableCell className="text-right tabular-nums text-foreground">{freq}</TableCell>
                      <TableCell className="text-right tabular-nums text-foreground">{formatCurrency(avgTicket)}</TableCell>
                      <TableCell className="text-center">
                        <Badge variant={badge.variant} dot>{badge.label}</Badge>
                      </TableCell>
                      <TableCell className="text-right text-muted text-xs">
                        {customer.rfv_last_order_at ? timeAgo(customer.rfv_last_order_at) : "\u2014"}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      {/* Drawer */}
      {selectedCustomer && (
        <div className="fixed inset-0 z-50 flex justify-end animate-fade-in">
          <div className="absolute inset-0 bg-black/50" onClick={() => setSelectedCustomer(null)} />
          <div className="relative w-full max-w-md bg-background-secondary border-l border-border h-full overflow-y-auto animate-slide-in-right shadow-elevation-4">
            {/* Drawer header */}
            <div className="sticky top-0 bg-background-secondary/95 backdrop-blur-sm border-b border-border p-5 flex items-center justify-between z-10">
              <div>
                <h2 className="text-base font-semibold text-foreground">{selectedCustomer.name || "Anonimo"}</h2>
                <Badge variant={getRFVBadge(selectedCustomer).variant} dot className="mt-1">{getRFVBadge(selectedCustomer).label}</Badge>
              </div>
              <button onClick={() => setSelectedCustomer(null)} className="w-8 h-8 flex items-center justify-center rounded-lg text-muted hover:text-foreground hover:bg-surface transition-colors">
                <X size={18} />
              </button>
            </div>

            {drawerLoading ? (
              <div className="flex items-center justify-center p-12"><LoadingSpinner size="md" /></div>
            ) : (
              <div className="p-5 space-y-6">
                {/* Info */}
                <section>
                  <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-3">Informacoes</h3>
                  <div className="bg-surface/50 rounded-lg p-4 space-y-3 text-sm">
                    {[
                      { label: "Telefone", value: selectedCustomer.phone },
                      { label: "E-mail", value: selectedCustomer.email },
                      { label: "Desde", value: new Intl.DateTimeFormat("pt-BR").format(new Date(selectedCustomer.created_at)) },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex justify-between">
                        <span className="text-muted">{label}</span>
                        <span className="text-foreground">{value || "\u2014"}</span>
                      </div>
                    ))}
                  </div>
                </section>

                {/* RFV */}
                <section>
                  <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-3">Score RFV</h3>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { label: "Recencia", value: selectedCustomer.rfv_recency_days ?? "\u2014", sub: "dias" },
                      { label: "Frequencia", value: selectedCustomer.rfv_frequency ?? "\u2014", sub: "pedidos" },
                      { label: "Monetario", value: selectedCustomer.rfv_monetary_cents != null ? formatCurrency(selectedCustomer.rfv_monetary_cents / 100) : "\u2014" },
                    ].map(({ label, value, sub }) => (
                      <div key={label} className="bg-surface/50 rounded-lg p-3.5 text-center">
                        <p className="text-xs text-muted mb-1">{label}</p>
                        <p className="text-lg font-semibold text-foreground tabular-nums">{value}</p>
                        {sub && <p className="text-xs text-muted">{sub}</p>}
                      </div>
                    ))}
                  </div>
                </section>

                {/* LGPD */}
                <section>
                  <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-3">Consentimentos LGPD</h3>
                  <div className="bg-surface/50 rounded-lg p-4 space-y-2.5">
                    {selectedCustomer.consent_summary && Object.keys(selectedCustomer.consent_summary).length > 0 ? (
                      Object.entries(selectedCustomer.consent_summary).map(([channel, granted]) => (
                        <div key={channel} className="flex items-center justify-between text-sm">
                          <span className="text-muted uppercase text-xs">{channel}</span>
                          <span className={`flex items-center gap-1.5 text-xs ${granted ? "text-emerald-400" : "text-red-400"}`}>
                            {granted ? <ShieldCheck size={13} /> : <ShieldOff size={13} />}
                            {granted ? "Concedido" : "Revogado"}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-muted text-xs">Nenhum consentimento registrado</p>
                    )}
                  </div>
                </section>

                {/* Consent history */}
                {drawerConsents.length > 0 && (
                  <section>
                    <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-3">Historico de consentimentos</h3>
                    <div className="space-y-1.5 max-h-40 overflow-y-auto">
                      {drawerConsents.slice(0, 10).map((c) => (
                        <div key={c.id} className="flex items-center justify-between text-xs bg-surface/50 rounded-lg px-3.5 py-2.5">
                          <span className="text-muted uppercase">{c.channel}</span>
                          <span className={c.status === "GRANTED" ? "text-emerald-400" : "text-red-400"}>
                            {c.status === "GRANTED" ? "Concedido" : "Revogado"}
                          </span>
                          <span className="text-muted tabular-nums">
                            {new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(c.created_at))}
                          </span>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Events */}
                <section>
                  <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-3">Eventos recentes</h3>
                  {drawerEvents.length === 0 ? (
                    <p className="text-muted text-xs">Nenhum evento</p>
                  ) : (
                    <div className="space-y-1.5 max-h-60 overflow-y-auto">
                      {drawerEvents.slice(0, 15).map((ev) => (
                        <div key={ev.id} className="flex items-center justify-between text-xs bg-surface/50 rounded-lg px-3.5 py-2.5">
                          <span className="text-foreground-secondary">{ev.event_type.replace(/_/g, " ")}</span>
                          <span className="text-muted">{timeAgo(ev.occurred_at)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
