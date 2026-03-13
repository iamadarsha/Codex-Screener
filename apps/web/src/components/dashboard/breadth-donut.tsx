"use client";

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { MarketBreadth } from "@/lib/api-types";

const COLORS = {
  advances: "#00c796",
  declines: "#ff5a8a",
  unchanged: "#232d40",
};

interface BreadthDonutProps {
  breadth?: MarketBreadth;
}

export function BreadthDonut({ breadth }: BreadthDonutProps) {
  const data = [
    { name: "Advances", value: breadth?.advances ?? 0, color: COLORS.advances },
    { name: "Declines", value: breadth?.declines ?? 0, color: COLORS.declines },
    { name: "Unchanged", value: breadth?.unchanged ?? 0, color: COLORS.unchanged },
  ];

  const total = breadth?.total ?? 0;
  const ratio = breadth?.advance_decline_ratio ?? 0;

  return (
    <div className="glass-card rounded-panel p-5">
      <h3 className="mb-4 text-sm font-semibold text-text-primary">Market Breadth</h3>

      <div className="flex items-center gap-6">
        {/* Donut with center label */}
        <div className="relative h-40 w-40 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={65}
                paddingAngle={2}
                dataKey="value"
                strokeWidth={0}
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 12,
                  color: "var(--text-primary)",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* Center ratio text */}
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-lg font-bold tabular-nums text-text-primary">
              {ratio.toFixed(2)}
            </span>
            <span className="text-[10px] text-text-muted">A/D</span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-col gap-3 text-sm">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-bullish" />
            <span className="text-text-secondary">Advances</span>
            <span className="ml-auto font-mono tabular-nums text-text-primary">
              {breadth?.advances ?? 0}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-bearish" />
            <span className="text-text-secondary">Declines</span>
            <span className="ml-auto font-mono tabular-nums text-text-primary">
              {breadth?.declines ?? 0}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-border" />
            <span className="text-text-secondary">Unchanged</span>
            <span className="ml-auto font-mono tabular-nums text-text-primary">
              {breadth?.unchanged ?? 0}
            </span>
          </div>
          <div className="mt-2 border-t border-border-subtle pt-2">
            <div className="flex items-center justify-between text-xs text-text-secondary">
              <span>A/D Ratio</span>
              <span className="font-mono tabular-nums text-text-primary">
                {ratio.toFixed(2)}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs text-text-secondary">
              <span>Total</span>
              <span className="font-mono tabular-nums text-text-primary">{total}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
