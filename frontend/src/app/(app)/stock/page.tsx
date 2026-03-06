"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/shared/MetricCard";
import { EmptyState } from "@/components/shared/EmptyState";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Toast } from "@/components/ui/Toast";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/Table";
import api from "@/lib/api";
import {
  Package,
  AlertTriangle,
  ArrowDownCircle,
  ArrowUpCircle,
  RefreshCw,
  Plus,
} from "lucide-react";
import type { StockItem, StockAlert, PaginatedResponse, MovementType } from "@/types/api";

type StatusFilter = "all" | "alert" | "critical";

const UNIT_LABELS: Record<string, string> = {
  kg: "kg", g: "g", L: "L", mL: "mL", un: "un", cx: "cx", pct: "pct",
};

const MOVEMENT_TYPES: { value: MovementType; label: string }[] = [
  { value: "ENTRADA", label: "Entrada" },
  { value: "SAIDA", label: "Saida" },
  { value: "AJUSTE", label: "Ajuste" },
  { value: "PERDA", label: "Perda" },
  { value: "INVENTARIO", label: "Inventario" },
];

function getStockStatus(item: StockItem): { label: string; variant: "danger" | "warning" | "success" | "default"; key: StatusFilter } {
  if (!item.level) return { label: "N/A", variant: "default", key: "all" };
  const current = parseFloat(item.level.current_quantity);
  const min = parseFloat(item.minimum_stock);
  if (current <= 0) return { label: "Critico", variant: "danger", key: "critical" };
  if (current <= min) return { label: "Alerta", variant: "warning", key: "alert" };
  return { label: "OK", variant: "success", key: "all" };
}

export default function StockPage() {
  const [items, setItems] = useState<StockItem[]>([]);
  const [alerts, setAlerts] = useState<StockAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [showModal, setShowModal] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  const [movStockItem, setMovStockItem] = useState("");
  const [movType, setMovType] = useState<MovementType>("ENTRADA");
  const [movQty, setMovQty] = useState("");
  const [movNotes, setMovNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [itemsRes, alertsRes] = await Promise.all([
        api.get<StockItem[] | PaginatedResponse<StockItem>>("/stock/items/"),
        api.get<StockAlert[] | PaginatedResponse<StockAlert>>("/stock/alerts/?open=true"),
      ]);
      const itemsData = Array.isArray(itemsRes.data) ? itemsRes.data : itemsRes.data.results;
      const alertsData = Array.isArray(alertsRes.data) ? alertsRes.data : alertsRes.data.results;
      setItems(itemsData);
      setAlerts(alertsData);
    } catch {
      setItems([]);
      setAlerts([]);
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

  const filteredItems = items.filter((item) => {
    if (filter === "all") return true;
    const status = getStockStatus(item);
    if (filter === "alert") return status.key === "alert" || status.key === "critical";
    return status.key === "critical";
  });

  async function handleSubmitMovement() {
    if (!movStockItem || !movQty) return;
    setSubmitting(true);
    try {
      await api.post("/stock/movements/", {
        stock_item: movStockItem,
        type: movType,
        quantity: parseFloat(movQty),
        notes: movNotes,
      });
      setToast({ type: "success", msg: "Movimentacao registrada" });
      setShowModal(false);
      setMovStockItem("");
      setMovType("ENTRADA");
      setMovQty("");
      setMovNotes("");
      fetchData();
    } catch {
      setToast({ type: "error", msg: "Erro ao registrar movimentacao" });
    } finally {
      setSubmitting(false);
    }
  }

  const totalItems = items.length;
  const alertCount = alerts.length;
  const criticalCount = items.filter((i) => getStockStatus(i).key === "critical").length;
  const filters: { key: StatusFilter; label: string }[] = [
    { key: "all", label: "Todos" },
    { key: "alert", label: "Alertas" },
    { key: "critical", label: "Criticos" },
  ];

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        title="Estoque"
        subtitle="Controle de inventario"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => { setLoading(true); fetchData(); }} icon={<RefreshCw className="w-3.5 h-3.5" />}>
              Atualizar
            </Button>
            <Button size="sm" onClick={() => setShowModal(true)} icon={<Plus className="w-3.5 h-3.5" />}>
              Nova Movimentacao
            </Button>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto">
        {/* Toast */}
        {toast && (
          <div className="px-6 pt-4">
            <Toast variant={toast.type === "success" ? "success" : "error"} message={toast.msg} onClose={() => setToast(null)} />
          </div>
        )}

        {/* Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 p-6">
          <MetricCard label="Total de itens" value={totalItems} icon={Package} />
          <MetricCard label="Itens com alerta" value={alertCount} icon={AlertTriangle} accent={alertCount > 0 ? "yellow" : "default"} />
          <MetricCard label="Itens criticos" value={criticalCount} icon={ArrowDownCircle} accent={criticalCount > 0 ? "red" : "default"} />
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
        ) : filteredItems.length === 0 ? (
          <EmptyState
            icon={Package}
            title="Nenhum item encontrado"
            description={filter !== "all" ? "Nenhum item com esse status" : "Cadastre itens de estoque para comecar"}
          />
        ) : (
          <div className="px-6 pb-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Unidade</TableHead>
                  <TableHead className="text-right">Qtd. Atual</TableHead>
                  <TableHead className="text-right">Minimo</TableHead>
                  <TableHead className="text-center">Status</TableHead>
                  <TableHead className="text-right">Ult. Movimentacao</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map((item) => {
                  const status = getStockStatus(item);
                  const current = item.level ? parseFloat(item.level.current_quantity) : 0;
                  const lastMov = item.level?.last_movement_at;
                  return (
                    <TableRow key={item.id} hover>
                      <TableCell className="font-medium text-foreground">{item.name}</TableCell>
                      <TableCell className="text-muted">{UNIT_LABELS[item.unit] || item.unit}</TableCell>
                      <TableCell className="text-right tabular-nums text-foreground">{current.toFixed(2)}</TableCell>
                      <TableCell className="text-right tabular-nums text-muted">{parseFloat(item.minimum_stock).toFixed(2)}</TableCell>
                      <TableCell className="text-center">
                        <Badge variant={status.variant} dot>{status.label}</Badge>
                      </TableCell>
                      <TableCell className="text-right text-muted text-xs">
                        {lastMov
                          ? new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(lastMov))
                          : "\u2014"}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      {/* Modal */}
      <Modal
        open={showModal}
        onClose={() => setShowModal(false)}
        title="Nova Movimentacao"
        description="Registrar entrada, saida ou ajuste"
        icon={<ArrowUpCircle className="w-5 h-5 text-primary" />}
      >
        <div className="space-y-4">
          <Select label="Item" value={movStockItem} onChange={(e) => setMovStockItem(e.target.value)}>
            <option value="">Selecione um item</option>
            {items.map((item) => (
              <option key={item.id} value={item.id}>{item.name} ({UNIT_LABELS[item.unit] || item.unit})</option>
            ))}
          </Select>

          <Select label="Tipo" value={movType} onChange={(e) => setMovType(e.target.value as MovementType)}>
            {MOVEMENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </Select>

          <Input
            label="Quantidade"
            type="number"
            step="0.01"
            min="0"
            value={movQty}
            onChange={(e) => setMovQty(e.target.value)}
            placeholder="0.00"
          />

          <Input
            label="Observacao"
            type="text"
            value={movNotes}
            onChange={(e) => setMovNotes(e.target.value)}
            placeholder="Opcional"
          />

          <Button onClick={handleSubmitMovement} loading={submitting} disabled={!movStockItem || !movQty} className="w-full" size="lg">
            Registrar
          </Button>
        </div>
      </Modal>
    </div>
  );
}
