"use client";

import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Eye, EyeOff } from "lucide-react";

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
      setError("Credenciais inválidas. Verifique email e senha.");
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
          background: "radial-gradient(circle at 50% 40%, rgba(249,115,22,0.06) 0%, transparent 60%)",
        }}
      />

      <div className="relative z-10 w-full max-w-[420px] px-6">
        {/* Glass card */}
        <div className="glass-card rounded-2xl p-8 shadow-card">
          {/* Logo & Brand */}
          <div className="flex flex-col items-center gap-4 mb-10">
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

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="email"
                className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="input-luxury w-full h-12 px-4 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground placeholder:text-muted/50 focus:outline-none"
                placeholder="operador@restaurante.com"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-[11px] text-muted/80 uppercase tracking-[0.15em] mb-2 font-medium"
              >
                Senha
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="input-luxury w-full h-12 px-4 pr-12 bg-surface-2/80 border border-border-light/50 rounded-lg text-sm text-foreground placeholder:text-muted/50 focus:outline-none"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-foreground transition-colors p-1"
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
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
                  Entrar
                  <span aria-hidden="true" className="text-lg">&rarr;</span>
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <a
              href="/cadastro"
              className="text-xs text-muted hover:text-accent transition-colors"
            >
              Ainda nao tem conta? <span className="text-accent font-medium">Criar conta</span>
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
