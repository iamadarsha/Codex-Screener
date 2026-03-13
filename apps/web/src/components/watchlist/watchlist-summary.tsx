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
    { label: "Watching", value: count.toString(), icon: Eye, color: "text-accent" },
    { label: "Gainers", value: gainers.toString(), icon: TrendingUp, color: "text-bullish" },
    { label: "Losers", value: losers.toString(), icon: TrendingDown, color: "text-bearish" },
    {
      label: "Total Volume",
      value: totalVolume >= 1e7
        ? `${(totalVolume / 1e7).toFixed(1)}Cr`
        : totalVolume >= 1e5
          ? `${(totalVolume / 1e5).toFixed(1)}L`
          : totalVolume.toString(),
      icon: BarChart3,
      color: "text-warning",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="flex items-center gap-3">
          <div className={`rounded-lg bg-elevated p-2 ${stat.color}`}>
            <stat.icon className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-text-muted">
              {stat.label}
            </div>
            <div className="font-mono text-lg font-semibold text-text-primary">
              {stat.value}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
