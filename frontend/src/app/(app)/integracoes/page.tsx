"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Toast } from "@/components/ui/Toast";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { useAuthStore } from "@/store/auth";
import api from "@/lib/api";
import { Plug } from "lucide-react";

interface IntegrationStatus {
  store_id: string;
  ifood: { status: string; merchant_id?: string };
  ninetynine: { status: string; merchant_id?: string };
}

export default function IntegracoesPage() {
  const storeId = useAuthStore((s) => s.storeId);
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  const [showModal, setShowModal] = useState(false);
  const [appShopId, setAppShopId] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [modalError, setModalError] = useState("");

  const fetchStatus = useCallback(async () => {
    if (!storeId) { setLoading(false); return; }
    try {
      const { data } = await api.get(`/api/v1/connect/status/?store_id=${storeId}`);
      setStatus(data);
    } catch {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, [storeId]);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);
  useEffect(() => {
    if (toast) { const t = setTimeout(() => setToast(null), 4000); return () => clearTimeout(t); }
  }, [toast]);

  async function handleIfoodConnect() {
    if (!storeId) return;
    try {
      const { data } = await api.post("/api/v1/connect/ifood/start/", null, { headers: { "X-Store-ID": storeId } });
      if (data.authorization_url) window.location.href = data.authorization_url;
    } catch {
      setToast({ type: "error", msg: "Erro ao iniciar conexao com iFood" });
    }
  }

  async function handleIfoodDisconnect() {
    if (!storeId) return;
    try {
      await api.post("/api/v1/connect/ifood/disconnect/", null, { headers: { "X-Store-ID": storeId } });
      setToast({ type: "success", msg: "iFood desconectado" });
      fetchStatus();
    } catch {
      setToast({ type: "error", msg: "Erro ao desconectar iFood" });
    }
  }

  async function handle99FoodConnect() {
    if (!storeId || !appShopId.trim()) return;
    setConnecting(true);
    setModalError("");
    try {
      await api.post("/api/v1/connect/99food/connect/", { store_id: storeId, app_shop_id: appShopId.trim() });
      setToast({ type: "success", msg: "99Food conectado com sucesso!" });
      setShowModal(false);
      setAppShopId("");
      fetchStatus();
    } catch (err: unknown) {
      setModalError((err as { response?: { data?: { error?: string } } })?.response?.data?.error || "Erro ao conectar 99Food");
    } finally {
      setConnecting(false);
    }
  }

  async function handle99FoodDisconnect() {
    if (!storeId) return;
    try {
      await api.post("/api/v1/connect/99food/disconnect/", { store_id: storeId });
      setToast({ type: "success", msg: "99Food desconectado" });
      fetchStatus();
    } catch {
      setToast({ type: "error", msg: "Erro ao desconectar 99Food" });
    }
  }

  const ifoodConnected = status?.ifood?.status === "connected";
  const nnConnected = status?.ninetynine?.status === "connected";

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header title="Integracoes" subtitle="Conecte seus marketplaces" />

      <div className="flex-1 overflow-y-auto">
        {toast && (
          <div className="px-6 pt-4">
            <Toast variant={toast.type === "success" ? "success" : "error"} message={toast.msg} onClose={() => setToast(null)} />
          </div>
        )}

        {!storeId && (
          <div className="p-12 text-center text-muted text-sm">Selecione uma loja para ver as integracoes.</div>
        )}

        {loading && storeId && (
          <div className="flex items-center justify-center p-12"><LoadingSpinner size="md" /></div>
        )}

        {!loading && storeId && (
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-5 max-w-3xl">
            {/* iFood */}
            <Card padding="lg">
              <div className="flex items-center gap-4 mb-5">
                <div className="w-12 h-12 rounded-xl bg-[#EA1D2C]/10 flex items-center justify-center ring-1 ring-inset ring-[#EA1D2C]/20">
                  <span className="text-[#EA1D2C] font-bold text-lg">iF</span>
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-foreground">iFood</h3>
                  <p className="text-xs text-muted">Marketplace de delivery</p>
                </div>
                <Badge variant={ifoodConnected ? "success" : "default"} dot>
                  {ifoodConnected ? "Conectado" : "Desconectado"}
                </Badge>
              </div>

              {ifoodConnected && status?.ifood?.merchant_id && (
                <div className="text-xs text-muted bg-surface/50 rounded-lg px-3.5 py-2.5 mb-4 tabular-nums">
                  Merchant ID: {status.ifood.merchant_id}
                </div>
              )}

              {ifoodConnected ? (
                <Button variant="danger" size="sm" onClick={handleIfoodDisconnect} className="w-full">Desconectar</Button>
              ) : (
                <button onClick={handleIfoodConnect} className="w-full h-10 bg-[#EA1D2C] text-white text-sm font-semibold rounded-lg hover:bg-[#C51A26] transition-colors">
                  Conectar iFood
                </button>
              )}
            </Card>

            {/* 99Food */}
            <Card padding="lg">
              <div className="flex items-center gap-4 mb-5">
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center ring-1 ring-inset ring-amber-500/20">
                  <span className="text-amber-400 font-bold text-lg">99</span>
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-foreground">99Food</h3>
                  <p className="text-xs text-muted">Marketplace 99</p>
                </div>
                <Badge variant={nnConnected ? "success" : "default"} dot>
                  {nnConnected ? "Conectado" : "Desconectado"}
                </Badge>
              </div>

              {nnConnected && status?.ninetynine?.merchant_id && (
                <div className="text-xs text-muted bg-surface/50 rounded-lg px-3.5 py-2.5 mb-4 tabular-nums">
                  Merchant ID: {status.ninetynine.merchant_id}
                </div>
              )}

              {nnConnected ? (
                <Button variant="danger" size="sm" onClick={handle99FoodDisconnect} className="w-full">Desconectar</Button>
              ) : (
                <Button variant="accent" size="md" onClick={() => setShowModal(true)} className="w-full">Conectar 99Food</Button>
              )}
            </Card>
          </div>
        )}
      </div>

      {/* 99Food Modal */}
      <Modal open={showModal} onClose={() => { setShowModal(false); setModalError(""); setAppShopId(""); }} title="Conectar 99Food" description="Informe o AppShopID do painel 99Food" icon={<Plug className="w-5 h-5 text-primary" />}>
        <div className="space-y-4">
          <Input label="AppShopID" value={appShopId} onChange={(e) => setAppShopId(e.target.value)} placeholder="Ex: 123456" autoFocus />

          <a href="/docs/guia-99food" target="_blank" className="text-xs text-primary hover:underline">
            Como encontrar meu AppShopID &rarr;
          </a>

          {modalError && <Toast variant="error" message={modalError} />}

          <Button onClick={handle99FoodConnect} loading={connecting} disabled={!appShopId.trim()} className="w-full" size="lg">
            Conectar
          </Button>
        </div>
      </Modal>
    </div>
  );
}
