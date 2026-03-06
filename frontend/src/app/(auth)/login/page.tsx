"use client";

import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Toast } from "@/components/ui/Toast";
import { Eye, EyeOff, Mail, Lock } from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
    } catch {
      setError("Credenciais invalidas. Verifique email e senha.");
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
            Gerencie seu restaurante com
            <span className="text-primary"> inteligencia</span>
          </h2>
          <p className="text-base text-muted-light leading-relaxed mb-10 max-w-lg">
            Centralize pedidos do iFood e 99Food, organize sua cozinha com KDS,
            controle estoque e fidelize clientes — tudo em uma plataforma.
          </p>

          <div className="flex items-center gap-3">
            <div className="flex -space-x-2">
              {[
                "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&crop=face",
                "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=80&h=80&fit=crop&crop=face",
                "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=80&h=80&fit=crop&crop=face",
              ].map((src, i) => (
                <img key={i} src={src} alt="" className="w-8 h-8 rounded-full border-2 border-background-secondary object-cover" loading="lazy" />
              ))}
            </div>
            <p className="text-sm text-muted-light">
              Usado por <span className="text-foreground font-medium">+500 restaurantes</span>
            </p>
          </div>
        </div>
      </div>

      {/* Right — Login form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-[400px]">
          <div className="flex items-center gap-3 mb-10 lg:hidden">
            <img src="/assets/images/logo.png" alt="MesaMestre" width={40} height={40} className="rounded-xl" />
            <span className="text-lg font-semibold text-foreground">MesaMestre</span>
          </div>

          <div className="mb-8">
            <h1 className="text-2xl font-bold text-foreground mb-2">Bem-vindo de volta</h1>
            <p className="text-sm text-muted">Entre com suas credenciais para acessar o sistema.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="seu@email.com"
              leftIcon={<Mail className="w-4 h-4" />}
            />

            <Input
              label="Senha"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              placeholder="Digite sua senha"
              leftIcon={<Lock className="w-4 h-4" />}
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              }
            />

            {error && <Toast variant="error" message={error} />}

            <Button type="submit" loading={loading} className="w-full" size="lg">
              Entrar
            </Button>
          </form>

          <p className="text-center text-sm text-muted mt-8">
            Ainda nao tem conta?{" "}
            <Link href="/cadastro" className="text-primary font-medium hover:text-primary-400 transition-colors">
              Criar conta
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
