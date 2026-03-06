import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Neutrals — warm slate base (not pure black)
        background: "#0C1017",
        "background-secondary": "#111827",
        surface: "#1E293B",
        "surface-2": "#334155",
        "surface-3": "#475569",
        border: "rgba(148, 163, 184, 0.12)",
        "border-light": "rgba(148, 163, 184, 0.20)",

        // Primary — Emerald (fresh, trustworthy, modern)
        primary: {
          DEFAULT: "#10B981",
          50: "#ECFDF5",
          100: "#D1FAE5",
          200: "#A7F3D0",
          300: "#6EE7B7",
          400: "#34D399",
          500: "#10B981",
          600: "#059669",
          700: "#047857",
          800: "#065F46",
          900: "#064E3B",
        },

        // Accent — Amber/Gold (premium, restaurant, highlight)
        accent: {
          DEFAULT: "#F59E0B",
          50: "#FFFBEB",
          100: "#FEF3C7",
          200: "#FDE68A",
          300: "#FCD34D",
          400: "#FBBF24",
          500: "#F59E0B",
          600: "#D97706",
          700: "#B45309",
        },

        // Semantic
        success: { DEFAULT: "#10B981", light: "#D1FAE5" },
        warning: { DEFAULT: "#F59E0B", light: "#FEF3C7" },
        danger: { DEFAULT: "#EF4444", light: "#FEE2E2" },
        info: { DEFAULT: "#3B82F6", light: "#DBEAFE" },

        // Text
        foreground: "#F1F5F9",
        "foreground-secondary": "#CBD5E1",
        muted: "#64748B",
        "muted-light": "#94A3B8",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "JetBrains Mono", "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.875rem" }],
      },
      borderRadius: {
        DEFAULT: "8px",
        sm: "6px",
        lg: "12px",
        xl: "16px",
      },
      boxShadow: {
        "elevation-1": "0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2)",
        "elevation-2": "0 4px 6px rgba(0, 0, 0, 0.3), 0 2px 4px rgba(0, 0, 0, 0.2)",
        "elevation-3": "0 10px 15px rgba(0, 0, 0, 0.3), 0 4px 6px rgba(0, 0, 0, 0.2)",
        "elevation-4": "0 20px 25px rgba(0, 0, 0, 0.3), 0 10px 10px rgba(0, 0, 0, 0.2)",
        glow: "0 0 20px rgba(16, 185, 129, 0.15)",
        "glow-lg": "0 0 40px rgba(16, 185, 129, 0.12)",
        "glow-accent": "0 0 20px rgba(245, 158, 11, 0.15)",
        card: "0 1px 3px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(148, 163, 184, 0.06)",
      },
      backdropBlur: {
        xs: "2px",
      },
      spacing: {
        "4.5": "1.125rem",
        "18": "4.5rem",
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-in-right": "slideInRight 0.25s ease-out",
        "slide-in-up": "slideInUp 0.2s ease-out",
        "scale-in": "scaleIn 0.15s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideInRight: {
          "0%": { transform: "translateX(100%)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        slideInUp: {
          "0%": { transform: "translateY(8px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        scaleIn: {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
