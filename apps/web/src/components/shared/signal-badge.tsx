"use client";

import { cn } from "@/lib/cn";

const SIGNAL_COLORS: Record<string, string> = {
  BREAKOUT: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  RSI: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  EMA: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  MACD: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  VOLUME: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  PATTERN: "bg-blue-500/20 text-blue-400 border-blue-500/30",
};

export function SignalBadge({ signal }: { signal: string }) {
  const colors =
    SIGNAL_COLORS[signal.toUpperCase()] ??
    "bg-gray-500/20 text-gray-400 border-gray-500/30";
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
        colors
      )}
    >
      {signal}
    </span>
  );
}
