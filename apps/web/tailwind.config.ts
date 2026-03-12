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
        accent: "var(--accent)",
        bullish: "var(--bullish)",
        bearish: "var(--bearish)",
        warning: "var(--warning)",
        info: "var(--info)",
      },
      boxShadow: {
        card: "0 4px 20px rgba(0, 0, 0, 0.4)",
        accent: "0 4px 16px rgba(124, 92, 252, 0.2)",
      },
      borderRadius: {
        panel: "12px",
      },
      fontFamily: {
        sans: ["var(--font-inter)"],
        mono: ["var(--font-jetbrains-mono)"],
      },
    },
  },
  plugins: [],
};

export default config;

