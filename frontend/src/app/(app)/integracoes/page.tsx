"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useAuthStore } from "@/store/auth";
import api from "@/lib/api";
import { Plug, X } from "lucide-react";

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

  // 99Food modal
  const [showModal, setShowModal] = useState(false);
  const [appShopId, setAppShopId] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [modalError, setModalError] = useState("");

  const fetchStatus = useCallback(async () => {
    if (!storeId) {
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get(`/api/v1/connect/status/?store_id=${storeId}`);
      setStatus(data);
    } catch {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, [storeId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(t);
    }
  }, [toast]);

  // iFood connect
  async function handleIfoodConnect() {
    if (!storeId) return;
    try {
      const { data } = await api.post("/api/v1/connect/ifood/start/", null, {
        headers: { "X-Store-ID": storeId },
      });
      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      }
    } catch {
      setToast({ type: "error", msg: "Erro ao iniciar conexao com iFood" });
    }
  }

  // iFood disconnect
  async function handleIfoodDisconnect() {
    if (!storeId) return;
    try {
      await api.post("/api/v1/connect/ifood/disconnect/", null, {
        headers: { "X-Store-ID": storeId },
      });
      setToast({ type: "success", msg: "iFood desconectado" });
      fetchStatus();
    } catch {
      setToast({ type: "error", msg: "Erro ao desconectar iFood" });
    }
  }

  // 99Food connect
  async function handle99FoodConnect() {
    if (!storeId || !appShopId.trim()) return;
    setConnecting(true);
    setModalError("");
    try {
      await api.post("/api/v1/connect/99food/connect/", {
        store_id: storeId,
        app_shop_id: appShopId.trim(),
      });
      setToast({ type: "success", msg: "99Food conectado com sucesso!" });
      setShowModal(false);
      setAppShopId("");
      fetchStatus();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
        "Erro ao conectar 99Food";
      setModalError(msg);
    } finally {
      setConnecting(false);
    }
  }

  // 99Food disconnect
  async function handle99FoodDisconnect() {
    if (!storeId) return;
    try {
      await api.post("/api/v1/connect/99food/disconnect/", {
        store_id: storeId,
      });
      setToast({ type: "success", msg: "99Food desconectado" });
      fetchStatus();
    } catch {
      setToast({ type: "error", msg: "Erro ao desconectar 99Food" });
    }
  }

  const ifoodConnected = status?.ifood?.status === "connected";
  const nnConnected = status?.ninetynine?.status === "connected";

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <Header title="Integracoes" />

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

      {!storeId && (
        <div className="p-6 text-center text-muted text-sm">
          Selecione uma loja para ver as integracoes.
        </div>
      )}

      {loading && storeId && (
        <div className="flex items-center justify-center p-12">
          <LoadingSpinner size="md" />
        </div>
      )}

      {!loading && storeId && (
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
          {/* iFood Card */}
          <div className="glass-card rounded-xl p-6 flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-[#EA1D2C]/10 flex items-center justify-center">
                <span className="text-[#EA1D2C] font-bold text-lg font-mono">iF</span>
              </div>
              <div>
                <h3 className="text-foreground font-semibold">iFood</h3>
                <p className="text-xs text-muted">Marketplace de delivery</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${ifoodConnected ? "bg-success" : "bg-muted/50"}`}
              />
              <span className={`text-sm ${ifoodConnected ? "text-success" : "text-muted"}`}>
                {ifoodConnected ? "Conectado" : "Nao conectado"}
              </span>
            </div>

            {ifoodConnected && status?.ifood?.merchant_id && (
              <div className="text-xs text-muted font-mono bg-surface-2 rounded px-3 py-2">
                Merchant ID: {status.ifood.merchant_id}
              </div>
            )}

            {ifoodConnected ? (
              <button
                onClick={handleIfoodDisconnect}
                className="mt-auto w-full h-10 border border-danger/30 text-danger text-sm rounded-lg hover:bg-danger/10 transition-colors"
              >
                Desconectar
              </button>
            ) : (
              <button
                onClick={handleIfoodConnect}
                className="mt-auto w-full h-10 bg-[#EA1D2C] text-white text-sm font-semibold rounded-lg hover:bg-[#C51A26] transition-colors"
              >
                Conectar iFood
              </button>
            )}
          </div>

          {/* 99Food Card */}
          <div className="glass-card rounded-xl p-6 flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
                <span className="text-accent font-bold text-lg font-mono">99</span>
              </div>
              <div>
                <h3 className="text-foreground font-semibold">99Food</h3>
                <p className="text-xs text-muted">Marketplace 99</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${nnConnected ? "bg-success" : "bg-muted/50"}`}
              />
              <span className={`text-sm ${nnConnected ? "text-success" : "text-muted"}`}>
                {nnConnected ? "Conectado" : "Nao conectado"}
              </span>
            </div>

            {nnConnected && status?.ninetynine?.merchant_id && (
              <div className="text-xs text-muted font-mono bg-surface-2 rounded px-3 py-2">
                Merchant ID: {status.ninetynine.merchant_id}
              </div>
            )}

            {nnConnected ? (
              <button
                onClick={handle99FoodDisconnect}
                className="mt-auto w-full h-10 border border-danger/30 text-danger text-sm rounded-lg hover:bg-danger/10 transition-colors"
              >
                Desconectar
              </button>
            ) : (
              <button
                onClick={() => setShowModal(true)}
                className="mt-auto w-full h-10 bg-gradient-to-r from-accent to-orange-500 text-black text-sm font-semibold rounded-lg hover:shadow-glow transition-all"
              >
                Conectar 99Food
              </button>
            )}
          </div>
        </div>
      )}

      {/* 99Food Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-card rounded-2xl p-6 w-full max-w-md mx-4 relative">
            <button
              onClick={() => {
                setShowModal(false);
                setModalError("");
                setAppShopId("");
              }}
              className="absolute top-4 right-4 text-muted hover:text-foreground"
            >
              <X size={20} />
            </button>

            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                <Plug className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h3 className="text-foreground font-semibold">Conectar 99Food</h3>
                <p className="text-xs text-muted">Informe o AppShopID do painel 99Food</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label
                  htmlFor="appShopId"
                  className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium"
                >
                  AppShopID
                </label>
                <input
                  id="appShopId"
                  type="text"
                  value={appShopId}
                  onChange={(e) => setAppShopId(e.target.value)}
                  placeholder="Ex: 123456"
                  className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground placeholder:text-muted/50 focus:outline-none"
                  autoFocus
                />
              </div>

              <a
                href="/docs/guia-99food"
                target="_blank"
                className="text-xs text-accent hover:underline"
              >
                Como encontrar meu AppShopID &rarr;
              </a>

              {modalError && (
                <div className="flex items-center gap-2 text-xs text-danger bg-danger/5 border border-danger/10 rounded-lg px-4 py-3">
                  <svg
                    className="w-4 h-4 shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 9v2m0 4h.01M12 3a9 9 0 100 18 9 9 0 000-18z"
                    />
                  </svg>
                  {modalError}
                </div>
              )}

              <button
                onClick={handle99FoodConnect}
                disabled={connecting || !appShopId.trim()}
                className="btn-shimmer w-full h-12 bg-gradient-to-r from-accent to-orange-500 text-black font-semibold text-sm rounded-lg hover:shadow-glow transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {connecting ? <LoadingSpinner size="sm" /> : "Conectar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
