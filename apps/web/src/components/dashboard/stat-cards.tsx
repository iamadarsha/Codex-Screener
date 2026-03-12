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
      color: "text-[#00c796]",
      borderGrad: "from-[#00c796] to-[#00c796]/0",
      bgGlow: "from-[rgba(0,199,150,0.06)]",
    },
    {
      label: "Triggered Alerts",
      value: alertCount,
      icon: Bell,
      color: "text-[#7c5cfc]",
      borderGrad: "from-[#7c5cfc] to-[#7c5cfc]/0",
      bgGlow: "from-[rgba(124,92,252,0.06)]",
    },
    {
      label: "Volume Surges",
      value: volumeSurgeCount,
      icon: BarChart3,
      color: "text-[#ff8800]",
      borderGrad: "from-[#ff8800] to-[#ff8800]/0",
      bgGlow: "from-[rgba(255,136,0,0.06)]",
    },
    {
      label: "Market Breadth",
      value: breadthPct,
      icon: Eye,
      color: breadthPct >= 50 ? "text-[#00c796]" : "text-[#ff5a8a]",
      borderGrad:
        breadthPct >= 50
          ? "from-[#00c796] to-[#00c796]/0"
          : "from-[#ff5a8a] to-[#ff5a8a]/0",
      bgGlow:
        breadthPct >= 50
          ? "from-[rgba(0,199,150,0.06)]"
          : "from-[rgba(255,90,138,0.06)]",
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
              <div className="text-[11px] font-medium uppercase tracking-wider text-[#8b95a8]">
                {card.label}
              </div>
              <div className="mt-3 flex items-baseline gap-1">
                <AnimatedNumber
                  value={card.value}
                  format={(v) => Math.round(v).toString()}
                  className="text-3xl font-semibold tabular-nums text-white"
                />
                {card.suffix && (
                  <span className="text-lg font-semibold text-[#8b95a8]">
                    {card.suffix}
                  </span>
                )}
              </div>
            </div>
            <div
              className={cn(
                "rounded-xl bg-[#1c2333] p-2.5 transition group-hover:scale-110",
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
