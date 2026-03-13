"use client";

import { useMarketIndices } from "@/hooks/use-market-breadth";
import { formatPrice, formatPercent } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { IndexData } from "@/lib/api-types";

function TickerItem({ index }: { index: IndexData }) {
  const last = index.last ?? index.value ?? 0;
  return (
    <div className="flex shrink-0 items-center gap-2 px-4">
      <span className="text-[11px] font-medium text-text-muted whitespace-nowrap">
        {index.name ?? index.symbol}
      </span>
      <span className="font-mono text-xs tabular-nums text-text-primary">
        {formatPrice(last)}
      </span>
      <span
        className={cn(
          "font-mono text-[11px] tabular-nums",
          index.change_pct >= 0 ? "text-bullish" : "text-bearish"
        )}
      >
        {formatPercent(index.change_pct)}
      </span>
    </div>
  );
}

export function IndexTickerBar() {
  const { data: indices } = useMarketIndices();

  if (!indices || indices.length === 0) return null;

  return (
    <div className="overflow-hidden border-b border-border-subtle bg-page/60">
      <div
        className="flex whitespace-nowrap py-1.5"
        style={{
          animation: "ticker-scroll 30s linear infinite",
          width: "max-content",
        }}
      >
        {/* Duplicate for seamless loop */}
        {indices.map((idx) => (
          <TickerItem key={idx.symbol} index={idx} />
        ))}
        {indices.map((idx) => (
          <TickerItem key={`dup-${idx.symbol}`} index={idx} />
        ))}
      </div>
    </div>
  );
}
