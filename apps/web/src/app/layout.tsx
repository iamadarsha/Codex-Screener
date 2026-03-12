"use client";

import { Inter, JetBrains_Mono } from "next/font/google";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { getQueryClient } from "@/lib/query-client";
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

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  const queryClient = getQueryClient();

  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} dark`}>
      <head>
        <title>BreakoutScan</title>
        <meta
          name="description"
          content="India's real-time NSE/BSE breakout screener."
        />
      </head>
      <body className="min-h-screen bg-[#0a0e1a] font-sans text-[#e8ecf4] antialiased">
        <QueryClientProvider client={queryClient}>
          {children}
          <Toaster
            theme="dark"
            position="bottom-right"
            toastOptions={{
              style: {
                background: "#1c2333",
                border: "1px solid #232d40",
                color: "#e8ecf4",
              },
            }}
          />
        </QueryClientProvider>
      </body>
    </html>
  );
}
