"use client";

import { Activity, BellRing, BarChart3, TrendingUp } from "lucide-react";
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
      color: "text-[#00C896]",
      bgGlow: "from-[rgba(0,200,150,0.08)]",
    },
    {
      label: "Triggered Alerts",
      value: alertCount,
      icon: BellRing,
      color: "text-[#7C5CFC]",
      bgGlow: "from-[rgba(124,92,252,0.08)]",
    },
    {
      label: "Volume Surges",
      value: volumeSurgeCount,
      icon: BarChart3,
      color: "text-[#FFA502]",
      bgGlow: "from-[rgba(255,165,2,0.08)]",
    },
    {
      label: "Market Breadth",
      value: breadthPct,
      icon: Activity,
      color: breadthPct >= 50 ? "text-[#00C896]" : "text-[#FF4757]",
      bgGlow:
        breadthPct >= 50
          ? "from-[rgba(0,200,150,0.08)]"
          : "from-[rgba(255,71,87,0.08)]",
      suffix: "%",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <Card
          key={card.label}
          className={cn("relative overflow-hidden bg-gradient-to-br", card.bgGlow, "to-transparent")}
        >
          <div className="flex items-start justify-between">
            <div>
              <div className="text-xs font-medium uppercase tracking-wider text-[#8B8D9A]">
                {card.label}
              </div>
              <div className="mt-3 flex items-baseline gap-1">
                <AnimatedNumber
                  value={card.value}
                  format={(v) => Math.round(v).toString()}
                  className="text-3xl font-semibold text-white"
                />
                {card.suffix && (
                  <span className="text-lg font-semibold text-[#8B8D9A]">
                    {card.suffix}
                  </span>
                )}
              </div>
            </div>
            <div className={cn("rounded-lg bg-[#22232D] p-2", card.color)}>
              <card.icon className="h-5 w-5" />
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
