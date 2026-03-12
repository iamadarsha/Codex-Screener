import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        page: "var(--bg-page)",
        sidebar: "var(--bg-sidebar)",
        card: "var(--bg-card)",
        elevated: "var(--bg-elevated)",
        border: "var(--border)",
        "border-subtle": "var(--border-subtle)",
        accent: {
          DEFAULT: "var(--accent)",
          hover: "var(--accent-hover)",
          glow: "var(--accent-glow)",
        },
        bullish: "var(--bullish)",
        bearish: "var(--bearish)",
        warning: "var(--warning)",
        info: "var(--info)",
        "text-primary": "var(--text-primary)",
        "text-secondary": "var(--text-secondary)",
        "text-muted": "var(--text-muted)",
      },
      boxShadow: {
        card: "0 4px 24px rgba(0, 0, 0, 0.5)",
        accent: "0 4px 20px rgba(124, 92, 252, 0.25)",
        glow: "0 0 20px rgba(124, 92, 252, 0.15)",
      },
      borderRadius: {
        panel: "12px",
      },
      fontFamily: {
        sans: ["var(--font-inter)"],
        mono: ["var(--font-jetbrains-mono)"],
      },
      animation: {
        "flash-bullish": "flash-bullish 0.6s ease-out",
        "flash-bearish": "flash-bearish 0.6s ease-out",
        "pulse-dot": "pulse-dot 1.5s ease-in-out infinite",
        shimmer: "shimmer 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
