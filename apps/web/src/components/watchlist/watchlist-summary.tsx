"use client";

import { TrendingUp, TrendingDown, BarChart3, Eye } from "lucide-react";
import { Card } from "@/components/ui/card";
import type { LivePrice } from "@/lib/api-types";

interface WatchlistSummaryProps {
  prices: Record<string, LivePrice>;
  count: number;
}

export function WatchlistSummary({ prices, count }: WatchlistSummaryProps) {
  const priceList = Object.values(prices);
  const gainers = priceList.filter((p) => p.change_pct > 0).length;
  const losers = priceList.filter((p) => p.change_pct < 0).length;
  const totalVolume = priceList.reduce((sum, p) => sum + p.volume, 0);

  const stats = [
    { label: "Watching", value: count.toString(), icon: Eye, color: "text-[#7C5CFC]" },
    { label: "Gainers", value: gainers.toString(), icon: TrendingUp, color: "text-[#00C896]" },
    { label: "Losers", value: losers.toString(), icon: TrendingDown, color: "text-[#FF4757]" },
    {
      label: "Total Volume",
      value: totalVolume >= 1e7
        ? `${(totalVolume / 1e7).toFixed(1)}Cr`
        : totalVolume >= 1e5
          ? `${(totalVolume / 1e5).toFixed(1)}L`
          : totalVolume.toString(),
      icon: BarChart3,
      color: "text-[#FFA502]",
    },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="flex items-center gap-3">
          <div className={`rounded-lg bg-[#22232D] p-2 ${stat.color}`}>
            <stat.icon className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-[#5C5D6E]">
              {stat.label}
            </div>
            <div className="font-mono text-lg font-semibold text-white">
              {stat.value}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
