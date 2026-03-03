"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

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
  const plan = searchParams.get("plan") || "";
  const planLabel = PLAN_LABELS[plan] || "";

  const [form, setForm] = useState({
    nome: "",
    empresa: "",
    whatsapp: "",
    email: "",
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  function update(field: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/cadastro", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, plan }),
      });

      if (!res.ok) throw new Error("Erro ao enviar cadastro");
      setSuccess(true);
    } catch {
      setError("Erro ao enviar. Tente novamente ou entre em contato pelo WhatsApp.");
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center relative overflow-hidden">
        {/* Ambient glow effects */}
        <div className="ambient-glow bg-success top-[-100px] left-[-100px]" />
        <div className="ambient-glow bg-success/50 bottom-[-100px] right-[-100px]" />

        <div
          className="absolute inset-0"
          style={{
            background: "radial-gradient(circle at 50% 40%, rgba(34,197,94,0.06) 0%, transparent 60%)",
          }}
        />

        <div className="relative z-10 w-full max-w-[420px] px-6">
          <div className="glass-card rounded-2xl p-8 shadow-card text-center">
            <div className="relative w-20 h-20 mx-auto mb-6">
              <div className="absolute inset-0 bg-success/20 rounded-full blur-xl" />
              <div className="relative w-20 h-20 bg-success/10 border border-success/20 rounded-full flex items-center justify-center">
                <svg className="w-10 h-10 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <h1 className="text-2xl font-sans font-bold text-foreground mb-3">
              Cadastro recebido!
            </h1>
            <p className="text-muted text-sm mb-8 leading-relaxed">
              Entraremos em contato pelo WhatsApp em breve para configurar sua conta
              {planLabel && <> no plano <span className="text-accent font-semibold">{planLabel}</span></>}.
            </p>
            <a
              href="/"
              className="inline-block h-12 px-8 bg-surface-2 border border-border-light/50 rounded-lg text-sm text-foreground hover:border-accent hover:shadow-glow transition-all duration-300 leading-[3rem]"
            >
              Voltar ao site
            </a>
          </div>
        </div>
      </div>
    );
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
