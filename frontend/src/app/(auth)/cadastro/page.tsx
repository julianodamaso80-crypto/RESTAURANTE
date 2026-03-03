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
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              "linear-gradient(rgba(249,115,22,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(249,115,22,0.03) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
        <div className="relative z-10 w-full max-w-sm px-6 text-center">
          <div className="w-16 h-16 bg-success/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-mono font-bold text-foreground mb-3">
            Cadastro recebido!
          </h1>
          <p className="text-muted text-sm mb-8">
            Entraremos em contato pelo WhatsApp em breve para configurar sua conta
            {planLabel && <> no plano <span className="text-accent font-semibold">{planLabel}</span></>}.
          </p>
          <a
            href="/"
            className="inline-block h-10 px-6 bg-surface-2 border border-border rounded text-sm text-foreground hover:border-accent transition-colors leading-10"
          >
            Voltar ao site
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center relative overflow-hidden">
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(rgba(249,115,22,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(249,115,22,0.03) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative z-10 w-full max-w-sm px-6">
        {/* Logo */}
        <div className="flex flex-col items-center gap-3 mb-6">
          <img src="/assets/images/logo.png" alt="MesaMestre" width={64} height={64} className="rounded-lg" />
          <span className="text-xl font-mono font-bold text-foreground tracking-wider">
            MESAMESTRE
          </span>
        </div>

        {planLabel && (
          <p className="text-center text-sm text-muted mb-6">
            Plano selecionado: <span className="text-accent font-semibold">{planLabel}</span>
          </p>
        )}

        <h1 className="text-center text-lg font-mono font-bold text-foreground mb-6">
          Crie sua conta
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="nome" className="block text-xs text-muted uppercase tracking-wider mb-1.5">
              Seu nome
            </label>
            <input
              id="nome"
              type="text"
              value={form.nome}
              onChange={(e) => update("nome", e.target.value)}
              required
              autoComplete="name"
              className="w-full h-10 px-3 bg-surface-2 border border-border rounded text-sm text-foreground placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
              placeholder="Maria Silva"
            />
          </div>

          <div>
            <label htmlFor="empresa" className="block text-xs text-muted uppercase tracking-wider mb-1.5">
              Nome da empresa
            </label>
            <input
              id="empresa"
              type="text"
              value={form.empresa}
              onChange={(e) => update("empresa", e.target.value)}
              required
              autoComplete="organization"
              className="w-full h-10 px-3 bg-surface-2 border border-border rounded text-sm text-foreground placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
              placeholder="Restaurante Bom Sabor"
            />
          </div>

          <div>
            <label htmlFor="whatsapp" className="block text-xs text-muted uppercase tracking-wider mb-1.5">
              WhatsApp
            </label>
            <input
              id="whatsapp"
              type="tel"
              value={form.whatsapp}
              onChange={(e) => update("whatsapp", e.target.value)}
              required
              autoComplete="tel"
              className="w-full h-10 px-3 bg-surface-2 border border-border rounded text-sm text-foreground placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
              placeholder="(11) 99999-9999"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-xs text-muted uppercase tracking-wider mb-1.5">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              required
              autoComplete="email"
              className="w-full h-10 px-3 bg-surface-2 border border-border rounded text-sm text-foreground placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
              placeholder="maria@bomsabor.com.br"
            />
          </div>

          {error && (
            <p className="text-xs text-danger bg-danger/10 border border-danger/20 rounded px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full h-10 bg-accent text-black font-mono font-bold text-sm rounded hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <>
                Criar conta
                <span aria-hidden="true">&rarr;</span>
              </>
            )}
          </button>
        </form>

        <p className="text-center text-xs text-muted mt-6">
          Ja tem conta?{" "}
          <a href="/login" className="text-accent hover:underline">
            Entrar
          </a>
        </p>

        <p className="text-center text-xs text-muted mt-4">
          MesaMestre &copy; {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
}
