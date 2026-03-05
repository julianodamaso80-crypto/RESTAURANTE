"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useAuthStore } from "@/store/auth";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PLAN_LABELS: Record<string, string> = {
  starter: "Starter",
  pro: "Pro",
  enterprise: "Enterprise",
};

export default function CadastroPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <CadastroForm />
    </Suspense>
  );
}

function CadastroForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { setTokens, setUser, setTenant, setStore } = useAuthStore();
  const plan = searchParams.get("plan") || "";
  const planLabel = PLAN_LABELS[plan] || "";

  const [form, setForm] = useState({
    nome: "",
    empresa: "",
    whatsapp: "",
    email: "",
    senha: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function update(field: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const { data } = await axios.post(`${API_URL}/api/v1/auth/register/`, {
        nome_completo: form.nome,
        email: form.email,
        senha: form.senha,
        nome_restaurante: form.empresa,
        telefone: form.whatsapp,
      });

      // Save tokens and user info
      setTokens(data.access, data.refresh);
      setUser(data.user);
      if (data.tenant_id) setTenant(data.tenant_id);
      if (data.store_id) setStore(data.store_id);

      router.push("/operator");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
        "Erro ao criar conta. Tente novamente.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center relative overflow-hidden">
      {/* Ambient glow effects */}
      <div className="ambient-glow bg-accent top-[-100px] left-[-100px]" />
      <div className="ambient-glow bg-accent/50 bottom-[-100px] right-[-100px]" />

      {/* Subtle grid */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(rgba(249,115,22,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(249,115,22,0.02) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* Radial gradient overlay */}
      <div
        className="absolute inset-0"
        style={{
          background: "radial-gradient(circle at 50% 30%, rgba(249,115,22,0.06) 0%, transparent 60%)",
        }}
      />

      <div className="relative z-10 w-full max-w-[420px] px-6 py-8">
        {/* Glass card */}
        <div className="glass-card rounded-2xl p-8 shadow-card">
          {/* Logo & Brand */}
          <div className="flex flex-col items-center gap-4 mb-6">
            <div className="relative">
              <div className="absolute inset-0 bg-accent/20 rounded-xl blur-xl" />
              <img
                src="/assets/images/logo.png"
                alt="Mesa Mestre"
                width={72}
                height={72}
                className="relative rounded-xl shadow-glow"
              />
            </div>
            <div className="text-center">
              <h1 className="text-2xl font-sans font-bold text-foreground tracking-wide">
                MESA <span className="text-accent">MESTRE</span>
              </h1>
              <p className="text-xs text-muted mt-1 tracking-widest uppercase">
                Sistema para Restaurantes
              </p>
            </div>
          </div>

          {planLabel && (
            <div className="text-center mb-5 py-2 px-4 bg-accent/5 border border-accent/10 rounded-lg">
              <p className="text-sm text-muted">
                Plano selecionado: <span className="text-accent font-semibold">{planLabel}</span>
              </p>
            </div>
          )}

          <h2 className="text-center text-lg font-sans font-semibold text-foreground mb-6">
            Crie sua conta
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="nome" className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                Seu nome
              </label>
              <input
                id="nome"
                type="text"
                value={form.nome}
                onChange={(e) => update("nome", e.target.value)}
                required
                autoComplete="name"
                className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground placeholder:text-muted/50 focus:outline-none"
                placeholder="Maria Silva"
              />
            </div>

            <div>
              <label htmlFor="empresa" className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                Nome da empresa
              </label>
              <input
                id="empresa"
                type="text"
                value={form.empresa}
                onChange={(e) => update("empresa", e.target.value)}
                required
                autoComplete="organization"
                className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground placeholder:text-muted/50 focus:outline-none"
                placeholder="Restaurante Bom Sabor"
              />
            </div>

            <div>
              <label htmlFor="whatsapp" className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                WhatsApp
              </label>
              <input
                id="whatsapp"
                type="tel"
                value={form.whatsapp}
                onChange={(e) => update("whatsapp", e.target.value)}
                required
                autoComplete="tel"
                className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground placeholder:text-muted/50 focus:outline-none"
                placeholder="(11) 99999-9999"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                required
                autoComplete="email"
                className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground placeholder:text-muted/50 focus:outline-none"
                placeholder="maria@bomsabor.com.br"
              />
            </div>

            <div>
              <label htmlFor="senha" className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium">
                Senha
              </label>
              <input
                id="senha"
                type="password"
                value={form.senha}
                onChange={(e) => update("senha", e.target.value)}
                required
                minLength={6}
                autoComplete="new-password"
                className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground placeholder:text-muted/50 focus:outline-none"
                placeholder="Minimo 6 caracteres"
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 text-xs text-danger bg-danger/5 border border-danger/10 rounded-lg px-4 py-3">
                <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M12 3a9 9 0 100 18 9 9 0 000-18z" />
                </svg>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-shimmer w-full h-12 bg-gradient-to-r from-accent to-orange-500 text-black font-semibold text-sm rounded-lg hover:shadow-glow transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <LoadingSpinner size="sm" />
              ) : (
                <>
                  Criar conta
                  <span aria-hidden="true" className="text-lg">&rarr;</span>
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <a
              href="/login"
              className="text-xs text-muted hover:text-accent transition-colors"
            >
              Ja tem conta? <span className="text-accent font-medium">Entrar</span>
            </a>
          </div>
        </div>

        <p className="text-center text-[11px] text-muted/50 mt-6 tracking-wide">
          Mesa Mestre &copy; {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
}
