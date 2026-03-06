"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Toast } from "@/components/ui/Toast";
import { useAuthStore } from "@/store/auth";
import api from "@/lib/api";
import { User, Building2, Phone, Mail, Lock } from "lucide-react";
import Link from "next/link";

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
      const { data } = await api.post("/api/v1/auth/register/", {
        nome_completo: form.nome,
        email: form.email,
        senha: form.senha,
        nome_restaurante: form.empresa,
        telefone: form.whatsapp,
      });

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
    <div className="min-h-screen bg-background flex">
      {/* Left — Branding panel */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-[55%] relative overflow-hidden bg-background-secondary">
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-primary/8 blur-[120px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-accent/6 blur-[120px]" />

        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: "radial-gradient(circle, rgba(148,163,184,0.5) 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />

        <div className="relative z-10 flex flex-col justify-center px-16 xl:px-24 max-w-2xl">
          <div className="flex items-center gap-3 mb-12">
            <img src="/assets/images/logo.png" alt="MesaMestre" width={44} height={44} className="rounded-xl" />
            <span className="text-xl font-semibold text-foreground">MesaMestre</span>
          </div>

          <h2 className="text-3xl xl:text-4xl font-bold text-foreground leading-tight mb-4">
            Comece a transformar seu
            <span className="text-primary"> restaurante</span>
          </h2>
          <p className="text-base text-muted-light leading-relaxed mb-10 max-w-lg">
            Configure sua conta em menos de 2 minutos.
            Sem cartao de credito, sem compromisso. 14 dias gratis.
          </p>

          <div className="space-y-4">
            {[
              "Integracoes iFood e 99Food em 1 clique",
              "KDS digital para organizar sua cozinha",
              "Controle de estoque automatico",
              "CRM e fidelizacao de clientes",
            ].map((item) => (
              <div key={item} className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-primary/15 flex items-center justify-center shrink-0">
                  <svg className="w-3 h-3 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="text-sm text-foreground-secondary">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right — Cadastro form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-[400px]">
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <img src="/assets/images/logo.png" alt="MesaMestre" width={40} height={40} className="rounded-xl" />
            <span className="text-lg font-semibold text-foreground">MesaMestre</span>
          </div>

          <div className="mb-6">
            <h1 className="text-2xl font-bold text-foreground mb-2">Crie sua conta</h1>
            <p className="text-sm text-muted">Preencha os dados abaixo para comecar.</p>
          </div>

          {planLabel && (
            <div className="mb-5 py-2.5 px-4 bg-primary/5 border border-primary/15 rounded-lg">
              <p className="text-sm text-foreground-secondary">
                Plano selecionado: <span className="text-primary font-semibold">{planLabel}</span>
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Seu nome"
              type="text"
              value={form.nome}
              onChange={(e) => update("nome", e.target.value)}
              required
              autoComplete="name"
              placeholder="Maria Silva"
              leftIcon={<User className="w-4 h-4" />}
            />

            <Input
              label="Nome da empresa"
              type="text"
              value={form.empresa}
              onChange={(e) => update("empresa", e.target.value)}
              required
              autoComplete="organization"
              placeholder="Restaurante Bom Sabor"
              leftIcon={<Building2 className="w-4 h-4" />}
            />

            <Input
              label="WhatsApp"
              type="tel"
              value={form.whatsapp}
              onChange={(e) => update("whatsapp", e.target.value)}
              required
              autoComplete="tel"
              placeholder="(11) 99999-9999"
              leftIcon={<Phone className="w-4 h-4" />}
            />

            <Input
              label="Email"
              type="email"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              required
              autoComplete="email"
              placeholder="maria@bomsabor.com.br"
              leftIcon={<Mail className="w-4 h-4" />}
            />

            <Input
              label="Senha"
              type="password"
              value={form.senha}
              onChange={(e) => update("senha", e.target.value)}
              required
              minLength={6}
              autoComplete="new-password"
              placeholder="Minimo 6 caracteres"
              leftIcon={<Lock className="w-4 h-4" />}
            />

            {error && <Toast variant="error" message={error} />}

            <Button type="submit" loading={loading} className="w-full" size="lg">
              Criar conta
            </Button>
          </form>

          <p className="text-center text-sm text-muted mt-8">
            Ja tem conta?{" "}
            <Link href="/login" className="text-primary font-medium hover:text-primary-400 transition-colors">
              Entrar
            </Link>
          </p>

          <p className="text-center text-xs text-muted/60 mt-6">
            MesaMestre &copy; {new Date().getFullYear()}
          </p>
        </div>
      </div>
    </div>
  );
}
