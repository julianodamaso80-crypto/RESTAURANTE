"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/shared/MetricCard";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { QuotaBar } from "@/components/admin/QuotaBar";
import api from "@/lib/api";
import {
  Megaphone,
  Send,
  BarChart3,
  Plus,
  X,
  RefreshCw,
  Zap,
} from "lucide-react";
import type {
  Campaign,
  CampaignStatusType,
  CustomerSegment,
  CampaignTemplate,
  PaginatedResponse,
  BillingQuota,
} from "@/types/api";

const STATUS_CONFIG: Record<CampaignStatusType, { label: string; className: string }> = {
  DRAFT: { label: "Rascunho", className: "bg-muted/15 text-muted border-muted/30" },
  SCHEDULED: { label: "Agendada", className: "bg-blue-500/15 text-blue-500 border-blue-500/30" },
  RUNNING: { label: "Enviando", className: "bg-yellow-500/15 text-yellow-500 border-yellow-500/30" },
  COMPLETED: { label: "Enviada", className: "bg-green-500/15 text-green-500 border-green-500/30" },
  CANCELLED: { label: "Cancelada", className: "bg-red-500/15 text-red-500 border-red-500/30" },
};

const CHANNEL_OPTIONS = [
  { value: "WHATSAPP", label: "WhatsApp", stub: true },
  { value: "EMAIL", label: "Email", stub: true },
  { value: "SMS", label: "SMS", stub: true },
  { value: "PUSH", label: "Push", stub: true },
];

export default function CRMPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [segments, setSegments] = useState<CustomerSegment[]>([]);
  const [templates, setTemplates] = useState<CampaignTemplate[]>([]);
  const [quota, setQuota] = useState<BillingQuota | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);
  const [launching, setLaunching] = useState<string | null>(null);

  // Form
  const [formName, setFormName] = useState("");
  const [formSegment, setFormSegment] = useState("");
  const [formTemplate, setFormTemplate] = useState("");
  const [formSchedule, setFormSchedule] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [campaignsRes, segmentsRes, templatesRes, quotaRes] = await Promise.all([
        api.get<Campaign[] | PaginatedResponse<Campaign>>("/crm/campaigns/"),
        api.get<CustomerSegment[] | PaginatedResponse<CustomerSegment>>("/crm/segments/"),
        api.get<CampaignTemplate[] | PaginatedResponse<CampaignTemplate>>("/crm/templates/"),
        api.get<BillingQuota>("/crm/billing/quota/").catch(() => ({ data: null })),
      ]);
      const c = Array.isArray(campaignsRes.data) ? campaignsRes.data : campaignsRes.data.results;
      const s = Array.isArray(segmentsRes.data) ? segmentsRes.data : segmentsRes.data.results;
      const t = Array.isArray(templatesRes.data) ? templatesRes.data : templatesRes.data.results;
      setCampaigns(c);
      setSegments(s);
      setTemplates(t);
      setQuota(quotaRes.data);
    } catch {
      setCampaigns([]);
      setSegments([]);
      setTemplates([]);
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

  async function handleCreateCampaign() {
    if (!formName || !formSegment || !formTemplate) return;
    setSubmitting(true);
    try {
      await api.post("/crm/campaigns/", {
        name: formName,
        segment: formSegment,
        template: formTemplate,
        scheduled_at: formSchedule || null,
      });
      setToast({ type: "success", msg: "Campanha criada com sucesso" });
      setShowModal(false);
      setFormName("");
      setFormSegment("");
      setFormTemplate("");
      setFormSchedule("");
      fetchData();
    } catch {
      setToast({ type: "error", msg: "Erro ao criar campanha" });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLaunch(campaignId: string) {
    setLaunching(campaignId);
    try {
      await api.post(`/crm/campaigns/${campaignId}/launch/`);
      setToast({ type: "success", msg: "Campanha lancada!" });
      fetchData();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Erro ao lancar campanha";
      setToast({ type: "error", msg });
    } finally {
      setLaunching(null);
    }
  }

  const activeCampaigns = campaigns.filter(
    (c) => c.status === "RUNNING" || c.status === "SCHEDULED"
  ).length;
  const totalSent = campaigns.reduce(
    (sum, c) => sum + c.runs.reduce((s, r) => s + r.sent_count, 0),
    0
  );
  const totalDelivered = campaigns.reduce(
    (sum, c) => sum + c.runs.reduce((s, r) => s + r.delivered_count, 0),
    0
  );
  const avgRate = totalSent > 0 ? Math.round((totalDelivered / totalSent) * 100) : 0;
  const quotaRemaining = quota ? quota.max_contacts - quota.current_period_contacts : 0;

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <Header title="CRM // Campanhas" />

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
        <MetricCard label="Campanhas ativas" value={activeCampaigns} icon={Megaphone} />
        <MetricCard label="Disparos do mes" value={totalSent} icon={Send} />
        <MetricCard
          label="Taxa entrega"
          value={`${avgRate}%`}
          icon={BarChart3}
          accent={avgRate >= 80 ? "green" : avgRate >= 50 ? "yellow" : "default"}
        />
        <MetricCard
          label="Quota restante"
          value={quota ? quotaRemaining : "—"}
          icon={Zap}
          accent={quota?.is_blocked ? "red" : quota?.is_near_limit ? "yellow" : "default"}
        />
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border">
        <span className="text-muted text-xs font-mono">
          {campaigns.length} campanha{campaigns.length !== 1 ? "s" : ""}
        </span>
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
            Nova Campanha
          </button>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center p-12">
          <LoadingSpinner size="md" />
        </div>
      ) : campaigns.length === 0 ? (
        <EmptyState
          icon={Megaphone}
          title="Nenhuma campanha criada"
          description="Crie segmentos e templates para comecar a enviar campanhas"
        />
      ) : (
        <div className="p-4 space-y-3">
          {campaigns.map((campaign) => {
            const statusConfig = STATUS_CONFIG[campaign.status] || STATUS_CONFIG.DRAFT;
            const latestRun = campaign.runs.length > 0 ? campaign.runs[campaign.runs.length - 1] : null;
            const canLaunch = campaign.status === "DRAFT" || campaign.status === "SCHEDULED";
            const selectedTemplate = templates.find((t) => t.id === campaign.template);

            return (
              <div
                key={campaign.id}
                className="bg-surface border border-border rounded-lg p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-foreground font-medium truncate">
                        {campaign.name}
                      </h3>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 text-xs font-mono font-medium rounded border shrink-0 ${statusConfig.className}`}
                      >
                        {statusConfig.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted">
                      <span>
                        Segmento: <span className="text-foreground">{campaign.segment_name}</span>
                      </span>
                      <span>
                        Canal:{" "}
                        <span className="text-foreground">
                          {selectedTemplate?.channel || campaign.template_name}
                        </span>
                        <span className="ml-1 text-[10px] text-accent border border-accent/30 rounded px-1">
                          Em breve
                        </span>
                      </span>
                      {campaign.scheduled_at && (
                        <span>
                          Agendada:{" "}
                          <span className="text-foreground font-mono">
                            {new Intl.DateTimeFormat("pt-BR", {
                              day: "2-digit",
                              month: "2-digit",
                              hour: "2-digit",
                              minute: "2-digit",
                            }).format(new Date(campaign.scheduled_at))}
                          </span>
                        </span>
                      )}
                    </div>

                    {/* Run stats */}
                    {latestRun && (
                      <div className="flex items-center gap-4 mt-2 text-xs font-mono">
                        <span className="text-muted">
                          Alcance:{" "}
                          <span className="text-foreground">
                            {latestRun.total_recipients}
                          </span>
                        </span>
                        <span className="text-success">
                          Enviados: {latestRun.sent_count}
                        </span>
                        <span className="text-success">
                          Entregues: {latestRun.delivered_count}
                        </span>
                        {latestRun.failed_count > 0 && (
                          <span className="text-danger">
                            Falhas: {latestRun.failed_count}
                          </span>
                        )}
                        {latestRun.opted_out_count > 0 && (
                          <span className="text-warning">
                            Opt-out: {latestRun.opted_out_count}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {canLaunch && (
                    <button
                      onClick={() => handleLaunch(campaign.id)}
                      disabled={launching === campaign.id || !!quota?.is_blocked}
                      className="shrink-0 flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 bg-success/10 text-success border border-success/30 rounded hover:bg-success/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {launching === campaign.id ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <Send size={12} />
                      )}
                      Lancar
                    </button>
                  )}
                </div>
              </div>
            );
          })}

          {/* Quota bar */}
          <div className="mt-4">
            <QuotaBar />
          </div>
        </div>
      )}

      {/* Modal Nova Campanha */}
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
                <Megaphone className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h3 className="text-foreground font-semibold">Nova Campanha</h3>
                <p className="text-xs text-muted">Configure e agende sua campanha</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                  Nome
                </label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="Ex: Reativacao Janeiro"
                  className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground placeholder:text-muted/50 focus:outline-none"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                  Segmento
                </label>
                <select
                  value={formSegment}
                  onChange={(e) => setFormSegment(e.target.value)}
                  className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground focus:outline-none appearance-none"
                >
                  <option value="">Selecione um segmento</option>
                  {segments.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} (~{s.estimated_size} clientes)
                    </option>
                  ))}
                </select>
                {segments.length === 0 && (
                  <p className="text-xs text-muted mt-1">
                    Crie segmentos via API antes de criar campanhas
                  </p>
                )}
              </div>

              <div>
                <label className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                  Canal / Template
                </label>
                <select
                  value={formTemplate}
                  onChange={(e) => setFormTemplate(e.target.value)}
                  className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground focus:outline-none appearance-none"
                >
                  <option value="">Selecione um template</option>
                  {templates.map((t) => {
                    const ch = CHANNEL_OPTIONS.find((c) => c.value === t.channel);
                    return (
                      <option key={t.id} value={t.id}>
                        {t.name} ({ch?.label || t.channel}) {ch?.stub ? "- Em breve" : ""}
                      </option>
                    );
                  })}
                </select>
                {templates.length === 0 && (
                  <p className="text-xs text-muted mt-1">
                    Crie templates via API antes de criar campanhas
                  </p>
                )}
              </div>

              <div>
                <label className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                  Agendamento (opcional)
                </label>
                <input
                  type="datetime-local"
                  value={formSchedule}
                  onChange={(e) => setFormSchedule(e.target.value)}
                  className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground focus:outline-none"
                />
              </div>

              {quota?.is_blocked && (
                <div className="flex items-center gap-2 text-xs text-danger bg-danger/5 border border-danger/10 rounded-lg px-4 py-3">
                  Quota esgotada — disparos bloqueados. Contate o suporte para upgrade.
                </div>
              )}

              <button
                onClick={handleCreateCampaign}
                disabled={submitting || !formName || !formSegment || !formTemplate}
                className="btn-shimmer w-full h-12 bg-gradient-to-r from-accent to-orange-500 text-black font-semibold text-sm rounded-lg hover:shadow-glow transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {submitting ? <LoadingSpinner size="sm" /> : "Criar Campanha"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
