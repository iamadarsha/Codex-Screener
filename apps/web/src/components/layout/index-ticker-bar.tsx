"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/cn";
import { formatPrice, formatPercent } from "@/lib/format";

interface IndexTick {
  symbol: string;
  name: string;
  value: number;
  change_pct: number;
}

export function IndexTickerBar() {
  const [indices, setIndices] = useState<IndexTick[]>([]);

  useEffect(() => {
    async function fetchIndices() {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001"}/api/market/indices`
        );
        if (res.ok) {
          const data = await res.json();
          setIndices(
            (data ?? []).map((d: Record<string, unknown>) => ({
              symbol: d.symbol ?? "",
              name: d.name ?? d.symbol ?? "",
              value: Number(d.value ?? d.last ?? 0),
              change_pct: Number(d.change_pct ?? 0),
            }))
          );
        }
      } catch {
        // silently ignore — ticker is non-critical
      }
    }
    fetchIndices();
    const id = setInterval(fetchIndices, 30_000);
    return () => clearInterval(id);
  }, []);

  if (indices.length === 0) return null;

  return (
    <div className="flex w-full overflow-x-auto border-b border-border bg-card/60 px-4 py-1.5 text-[11px] scrollbar-hide">
      <div className="flex items-center gap-6 whitespace-nowrap">
        {indices.map((idx) => (
          <span key={idx.symbol} className="flex items-center gap-1.5">
            <span className="font-medium text-text-secondary">{idx.name}</span>
            <span className="font-mono text-text-primary">
              {formatPrice(idx.value)}
            </span>
            <span
              className={cn(
                "font-mono",
                idx.change_pct >= 0 ? "text-bullish" : "text-bearish"
              )}
            >
              {idx.change_pct >= 0 ? "+" : ""}
              {formatPercent(idx.change_pct)}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
