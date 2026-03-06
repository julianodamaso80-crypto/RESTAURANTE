"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { MetricCard } from "@/components/shared/MetricCard";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { QuotaBar } from "@/components/admin/QuotaBar";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Toast } from "@/components/ui/Toast";
import { Card } from "@/components/ui/Card";
import api from "@/lib/api";
import {
  Megaphone,
  Send,
  BarChart3,
  Plus,
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

const STATUS_CONFIG: Record<CampaignStatusType, { label: string; variant: "default" | "info" | "warning" | "success" | "danger" }> = {
  DRAFT: { label: "Rascunho", variant: "default" },
  SCHEDULED: { label: "Agendada", variant: "info" },
  RUNNING: { label: "Enviando", variant: "warning" },
  COMPLETED: { label: "Enviada", variant: "success" },
  CANCELLED: { label: "Cancelada", variant: "danger" },
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
      setCampaigns(Array.isArray(campaignsRes.data) ? campaignsRes.data : campaignsRes.data.results);
      setSegments(Array.isArray(segmentsRes.data) ? segmentsRes.data : segmentsRes.data.results);
      setTemplates(Array.isArray(templatesRes.data) ? templatesRes.data : templatesRes.data.results);
      setQuota(quotaRes.data);
    } catch {
      setCampaigns([]);
      setSegments([]);
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (toast) { const t = setTimeout(() => setToast(null), 4000); return () => clearTimeout(t); }
  }, [toast]);

  async function handleCreateCampaign() {
    if (!formName || !formSegment || !formTemplate) return;
    setSubmitting(true);
    try {
      await api.post("/crm/campaigns/", { name: formName, segment: formSegment, template: formTemplate, scheduled_at: formSchedule || null });
      setToast({ type: "success", msg: "Campanha criada com sucesso" });
      setShowModal(false);
      setFormName(""); setFormSegment(""); setFormTemplate(""); setFormSchedule("");
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
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Erro ao lancar campanha";
      setToast({ type: "error", msg });
    } finally {
      setLaunching(null);
    }
  }

  const activeCampaigns = campaigns.filter((c) => c.status === "RUNNING" || c.status === "SCHEDULED").length;
  const totalSent = campaigns.reduce((sum, c) => sum + c.runs.reduce((s, r) => s + r.sent_count, 0), 0);
  const totalDelivered = campaigns.reduce((sum, c) => sum + c.runs.reduce((s, r) => s + r.delivered_count, 0), 0);
  const avgRate = totalSent > 0 ? Math.round((totalDelivered / totalSent) * 100) : 0;
  const quotaRemaining = quota ? quota.max_contacts - quota.current_period_contacts : 0;

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        title="CRM"
        subtitle="Gestao de campanhas"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => { setLoading(true); fetchData(); }} icon={<RefreshCw className="w-3.5 h-3.5" />}>
              Atualizar
            </Button>
            <Button size="sm" onClick={() => setShowModal(true)} icon={<Plus className="w-3.5 h-3.5" />}>
              Nova Campanha
            </Button>
          </div>
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
          <MetricCard label="Campanhas ativas" value={activeCampaigns} icon={Megaphone} />
          <MetricCard label="Disparos do mes" value={totalSent} icon={Send} />
          <MetricCard label="Taxa entrega" value={`${avgRate}%`} icon={BarChart3} accent={avgRate >= 80 ? "green" : avgRate >= 50 ? "yellow" : "default"} />
          <MetricCard label="Quota restante" value={quota ? quotaRemaining : "\u2014"} icon={Zap} accent={quota?.is_blocked ? "red" : quota?.is_near_limit ? "yellow" : "default"} />
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center p-12"><LoadingSpinner size="md" /></div>
        ) : campaigns.length === 0 ? (
          <EmptyState
            icon={Megaphone}
            title="Nenhuma campanha criada"
            description="Crie segmentos e templates para comecar a enviar campanhas"
            action={<Button size="sm" onClick={() => setShowModal(true)} icon={<Plus className="w-3.5 h-3.5" />}>Nova Campanha</Button>}
          />
        ) : (
          <div className="px-6 pb-6 space-y-3">
            {campaigns.map((campaign) => {
              const statusConfig = STATUS_CONFIG[campaign.status] || STATUS_CONFIG.DRAFT;
              const latestRun = campaign.runs.length > 0 ? campaign.runs[campaign.runs.length - 1] : null;
              const canLaunch = campaign.status === "DRAFT" || campaign.status === "SCHEDULED";
              const selectedTemplate = templates.find((t) => t.id === campaign.template);

              return (
                <Card key={campaign.id} padding="md" hover>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2.5 mb-1.5">
                        <h3 className="text-sm font-semibold text-foreground truncate">{campaign.name}</h3>
                        <Badge variant={statusConfig.variant} dot>{statusConfig.label}</Badge>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted">
                        <span>Segmento: <span className="text-foreground-secondary">{campaign.segment_name}</span></span>
                        <span>
                          Canal: <span className="text-foreground-secondary">{selectedTemplate?.channel || campaign.template_name}</span>
                          <Badge variant="accent" className="ml-1.5 text-2xs">Em breve</Badge>
                        </span>
                        {campaign.scheduled_at && (
                          <span>
                            Agendada: <span className="text-foreground-secondary tabular-nums">
                              {new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(campaign.scheduled_at))}
                            </span>
                          </span>
                        )}
                      </div>

                      {latestRun && (
                        <div className="flex items-center gap-4 mt-2.5 text-xs">
                          <span className="text-muted">Alcance: <span className="text-foreground-secondary tabular-nums">{latestRun.total_recipients}</span></span>
                          <span className="text-emerald-400">Enviados: {latestRun.sent_count}</span>
                          <span className="text-emerald-400">Entregues: {latestRun.delivered_count}</span>
                          {latestRun.failed_count > 0 && <span className="text-red-400">Falhas: {latestRun.failed_count}</span>}
                          {latestRun.opted_out_count > 0 && <span className="text-amber-400">Opt-out: {latestRun.opted_out_count}</span>}
                        </div>
                      )}
                    </div>

                    {canLaunch && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleLaunch(campaign.id)}
                        loading={launching === campaign.id}
                        disabled={!!quota?.is_blocked}
                        icon={<Send className="w-3.5 h-3.5" />}
                      >
                        Lancar
                      </Button>
                    )}
                  </div>
                </Card>
              );
            })}

            <div className="mt-4"><QuotaBar /></div>
          </div>
        )}
      </div>

      {/* Modal */}
      <Modal open={showModal} onClose={() => setShowModal(false)} title="Nova Campanha" description="Configure e agende sua campanha" icon={<Megaphone className="w-5 h-5 text-primary" />}>
        <div className="space-y-4">
          <Input label="Nome" value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="Ex: Reativacao Janeiro" autoFocus />

          <Select label="Segmento" value={formSegment} onChange={(e) => setFormSegment(e.target.value)}>
            <option value="">Selecione um segmento</option>
            {segments.map((s) => <option key={s.id} value={s.id}>{s.name} (~{s.estimated_size} clientes)</option>)}
          </Select>
          {segments.length === 0 && <p className="text-xs text-muted">Crie segmentos via API antes de criar campanhas</p>}

          <Select label="Canal / Template" value={formTemplate} onChange={(e) => setFormTemplate(e.target.value)}>
            <option value="">Selecione um template</option>
            {templates.map((t) => {
              const ch = CHANNEL_OPTIONS.find((c) => c.value === t.channel);
              return <option key={t.id} value={t.id}>{t.name} ({ch?.label || t.channel}) {ch?.stub ? "- Em breve" : ""}</option>;
            })}
          </Select>
          {templates.length === 0 && <p className="text-xs text-muted">Crie templates via API antes de criar campanhas</p>}

          <Input label="Agendamento (opcional)" type="datetime-local" value={formSchedule} onChange={(e) => setFormSchedule(e.target.value)} />

          {quota?.is_blocked && (
            <Toast variant="error" message="Quota esgotada — disparos bloqueados. Contate o suporte para upgrade." />
          )}

          <Button onClick={handleCreateCampaign} loading={submitting} disabled={!formName || !formSegment || !formTemplate} className="w-full" size="lg">
            Criar Campanha
          </Button>
        </div>
      </Modal>
    </div>
  );
}
