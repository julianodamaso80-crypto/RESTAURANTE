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
        background: "#0A0A0A",
        surface: "#111111",
        "surface-2": "#1A1A1A",
        "surface-3": "#222222",
        border: "#2A2A2A",
        "border-light": "#3A3A3A",
        accent: "#F97316",
        "accent-gold": "#D4A853",
        success: "#22C55E",
        warning: "#EAB308",
        danger: "#EF4444",
        foreground: "#E5E5E5",
        muted: "#737373",
      },
      fontFamily: {
        mono: ["var(--font-jetbrains)", "JetBrains Mono", "monospace"],
        sans: ["var(--font-inter)", "Inter", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "4px",
      },
      boxShadow: {
        glow: "0 0 20px rgba(249,115,22,0.15)",
        "glow-lg": "0 0 40px rgba(249,115,22,0.1)",
        card: "0 8px 32px rgba(0,0,0,0.4)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
export default config;
