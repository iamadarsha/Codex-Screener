"use client";

import { TrendingUp, Bell, BarChart3, Eye } from "lucide-react";
import { Card } from "@/components/ui/card";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { cn } from "@/lib/cn";
import type { MarketBreadth } from "@/lib/api-types";

interface StatCardsProps {
  breakoutCount?: number;
  alertCount?: number;
  volumeSurgeCount?: number;
  breadth?: MarketBreadth;
}

export function StatCards({
  breakoutCount = 0,
  alertCount = 0,
  volumeSurgeCount = 0,
  breadth,
}: StatCardsProps) {
  const breadthPct = breadth
    ? Math.round((breadth.advances / Math.max(breadth.total, 1)) * 100)
    : 0;

  const cards = [
    {
      label: "Active Breakouts",
      value: breakoutCount,
      icon: TrendingUp,
      color: "text-bullish",
      borderGrad: "from-bullish to-bullish/0",
      bgGlow: "from-bullish/[0.06]",
    },
    {
      label: "Triggered Alerts",
      value: alertCount,
      icon: Bell,
      color: "text-accent",
      borderGrad: "from-accent to-accent/0",
      bgGlow: "from-accent/[0.06]",
    },
    {
      label: "Volume Surges",
      value: volumeSurgeCount,
      icon: BarChart3,
      color: "text-warning",
      borderGrad: "from-warning to-warning/0",
      bgGlow: "from-warning/[0.06]",
    },
    {
      label: "Market Breadth",
      value: breadthPct,
      icon: Eye,
      color: breadthPct >= 50 ? "text-bullish" : "text-bearish",
      borderGrad:
        breadthPct >= 50
          ? "from-bullish to-bullish/0"
          : "from-bearish to-bearish/0",
      bgGlow:
        breadthPct >= 50
          ? "from-bullish/[0.06]"
          : "from-bearish/[0.06]",
      suffix: "%",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <Card
          key={card.label}
          className={cn(
            "group relative overflow-hidden bg-gradient-to-br",
            card.bgGlow,
            "to-transparent"
          )}
        >
          {/* Top gradient border accent */}
          <div
            className={cn(
              "absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r",
              card.borderGrad
            )}
          />

          <div className="flex items-start justify-between">
            <div>
              <div className="text-[11px] font-medium uppercase tracking-wider text-text-secondary">
                {card.label}
              </div>
              <div className="mt-3 flex items-baseline gap-1">
                <AnimatedNumber
                  value={card.value}
                  format={(v) => Math.round(v).toString()}
                  className="text-3xl font-semibold tabular-nums text-text-primary"
                />
                {card.suffix && (
                  <span className="text-lg font-semibold text-text-secondary">
                    {card.suffix}
                  </span>
                )}
              </div>
            </div>
            <div
              className={cn(
                "rounded-xl bg-elevated p-2.5 transition group-hover:scale-110",
                card.color
              )}
            >
              <card.icon className="h-5 w-5" />
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
