"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { CHART_COLORS } from "@/lib/chart-colors";
import { formatVolume } from "@/lib/format";
import type { OHLCV } from "@/lib/api-types";

interface VolumePanelProps {
  candles: OHLCV[];
  height?: number;
}

export function VolumePanel({ candles, height = 120 }: VolumePanelProps) {
  const data = candles.slice(-60).map((c) => ({
    time: c.time,
    volume: c.volume,
    fill: c.close >= c.open ? CHART_COLORS.volumeUp : CHART_COLORS.volumeDown,
  }));

  return (
    <div className="rounded-panel border border-border bg-card p-4">
      <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-[#8B8D9A]">
        Volume
      </h4>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data}>
          <XAxis dataKey="time" hide />
          <YAxis
            hide
            domain={[0, "dataMax"]}
          />
          <Tooltip
            contentStyle={{
              background: "#1A1B23",
              border: "1px solid #2A2B35",
              borderRadius: 8,
              fontSize: 12,
              color: "#E8E9F0",
            }}
            formatter={(value: number) => [formatVolume(value), "Volume"]}
            labelFormatter={() => ""}
          />
          <Bar dataKey="volume" radius={[2, 2, 0, 0]}>
            {data.map((entry, idx) => (
              <rect key={idx} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
