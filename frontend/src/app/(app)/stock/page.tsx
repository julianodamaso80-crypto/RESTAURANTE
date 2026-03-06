"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/shared/MetricCard";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import api from "@/lib/api";
import {
  Package,
  AlertTriangle,
  ArrowDownCircle,
  ArrowUpCircle,
  RefreshCw,
  Plus,
  X,
} from "lucide-react";
import type { StockItem, StockAlert, PaginatedResponse, MovementType } from "@/types/api";

type StatusFilter = "all" | "alert" | "critical";

const UNIT_LABELS: Record<string, string> = {
  kg: "kg",
  g: "g",
  L: "L",
  mL: "mL",
  un: "un",
  cx: "cx",
  pct: "pct",
};

const MOVEMENT_TYPES: { value: MovementType; label: string }[] = [
  { value: "ENTRADA", label: "Entrada" },
  { value: "SAIDA", label: "Saida" },
  { value: "AJUSTE", label: "Ajuste" },
  { value: "PERDA", label: "Perda" },
  { value: "INVENTARIO", label: "Inventario" },
];

function getStockStatus(item: StockItem): { label: string; className: string; key: StatusFilter } {
  if (!item.level) return { label: "N/A", className: "bg-muted/15 text-muted border-muted/30", key: "all" };
  const current = parseFloat(item.level.current_quantity);
  const min = parseFloat(item.minimum_stock);
  if (current <= 0) return { label: "CRITICO", className: "bg-red-500/15 text-red-500 border-red-500/30", key: "critical" };
  if (current <= min) return { label: "ALERTA", className: "bg-yellow-500/15 text-yellow-500 border-yellow-500/30", key: "alert" };
  return { label: "OK", className: "bg-green-500/15 text-green-500 border-green-500/30", key: "all" };
}

export default function StockPage() {
  const [items, setItems] = useState<StockItem[]>([]);
  const [alerts, setAlerts] = useState<StockAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [showModal, setShowModal] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  // Movement form
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

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <Header title="Estoque" />

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
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 p-4 border-b border-border">
        <MetricCard label="Total de itens" value={totalItems} icon={Package} />
        <MetricCard
          label="Itens com alerta"
          value={alertCount}
          icon={AlertTriangle}
          accent={alertCount > 0 ? "yellow" : "default"}
        />
        <MetricCard
          label="Itens criticos"
          value={criticalCount}
          icon={ArrowDownCircle}
          accent={criticalCount > 0 ? "red" : "default"}
        />
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border">
        <div className="flex items-center gap-2">
          {(["all", "alert", "critical"] as StatusFilter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs font-mono px-3 py-1 rounded border transition-colors ${
                filter === f
                  ? "bg-accent/10 text-accent border-accent/30"
                  : "text-muted border-border hover:text-foreground hover:border-border-light"
              }`}
            >
              {f === "all" ? "Todos" : f === "alert" ? "Alertas" : "Criticos"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setLoading(true); fetchData(); }}
            className="text-muted hover:text-foreground transition-colors"
          >
            <RefreshCw size={14} />
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 bg-accent text-black rounded hover:bg-accent/90 transition-colors"
          >
            <Plus size={14} />
            Nova Movimentacao
          </button>
        </div>
      </div>

      {/* Tabela */}
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
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-muted text-xs font-mono uppercase tracking-wider">
                <th className="text-left px-4 py-3">Nome</th>
                <th className="text-left px-4 py-3">Unidade</th>
                <th className="text-right px-4 py-3">Qtd. Atual</th>
                <th className="text-right px-4 py-3">Minimo</th>
                <th className="text-center px-4 py-3">Status</th>
                <th className="text-right px-4 py-3">Ult. Movimentacao</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => {
                const status = getStockStatus(item);
                const current = item.level ? parseFloat(item.level.current_quantity) : 0;
                const lastMov = item.level?.last_movement_at;
                return (
                  <tr
                    key={item.id}
                    className="border-b border-border/50 hover:bg-surface-2/50 transition-colors"
                  >
                    <td className="px-4 py-3 text-foreground font-medium">{item.name}</td>
                    <td className="px-4 py-3 text-muted font-mono">
                      {UNIT_LABELS[item.unit] || item.unit}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-foreground">
                      {current.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-muted">
                      {parseFloat(item.minimum_stock).toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 text-xs font-mono font-medium rounded border ${status.className}`}
                      >
                        {status.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-muted text-xs font-mono">
                      {lastMov
                        ? new Intl.DateTimeFormat("pt-BR", {
                            day: "2-digit",
                            month: "2-digit",
                            hour: "2-digit",
                            minute: "2-digit",
                          }).format(new Date(lastMov))
                        : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal Nova Movimentacao */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-card rounded-2xl p-6 w-full max-w-md mx-4 relative">
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 text-muted hover:text-foreground"
            >
              <X size={20} />
            </button>

            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                <ArrowUpCircle className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h3 className="text-foreground font-semibold">Nova Movimentacao</h3>
                <p className="text-xs text-muted">Registrar entrada, saida ou ajuste</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                  Item
                </label>
                <select
                  value={movStockItem}
                  onChange={(e) => setMovStockItem(e.target.value)}
                  className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground focus:outline-none appearance-none"
                >
                  <option value="">Selecione um item</option>
                  {items.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name} ({UNIT_LABELS[item.unit] || item.unit})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                  Tipo
                </label>
                <select
                  value={movType}
                  onChange={(e) => setMovType(e.target.value as MovementType)}
                  className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground focus:outline-none appearance-none"
                >
                  {MOVEMENT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                  Quantidade
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={movQty}
                  onChange={(e) => setMovQty(e.target.value)}
                  placeholder="0.00"
                  className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground placeholder:text-muted/50 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                  Observacao
                </label>
                <input
                  type="text"
                  value={movNotes}
                  onChange={(e) => setMovNotes(e.target.value)}
                  placeholder="Opcional"
                  className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground placeholder:text-muted/50 focus:outline-none"
                />
              </div>

              <button
                onClick={handleSubmitMovement}
                disabled={submitting || !movStockItem || !movQty}
                className="btn-shimmer w-full h-12 bg-gradient-to-r from-accent to-orange-500 text-black font-semibold text-sm rounded-lg hover:shadow-glow transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {submitting ? <LoadingSpinner size="sm" /> : "Registrar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
