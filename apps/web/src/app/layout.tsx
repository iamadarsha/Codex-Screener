"use client";

import { Inter, JetBrains_Mono } from "next/font/google";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { getQueryClient } from "@/lib/query-client";
import { ThemeProvider, useTheme } from "@/components/providers/theme-provider";
import type { ReactNode } from "react";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

function ThemedToaster() {
  const { theme } = useTheme();
  return (
    <Toaster
      theme={theme}
      position="bottom-right"
      toastOptions={{
        style: {
          background: "var(--bg-elevated)",
          border: "1px solid var(--border)",
          color: "var(--text-primary)",
          backdropFilter: "blur(12px)",
        },
      }}
    />
  );
}

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  const queryClient = getQueryClient();

  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable}`}
      data-theme="dark"
      suppressHydrationWarning
    >
      <head>
        <title>BreakoutScan</title>
        <meta
          name="description"
          content="India's real-time NSE/BSE breakout screener."
        />
      </head>
      <body className="min-h-screen font-sans antialiased">
        <ThemeProvider>
          <QueryClientProvider client={queryClient}>
            {children}
            <ThemedToaster />
          </QueryClientProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
