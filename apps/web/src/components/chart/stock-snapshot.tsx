"use client";

import { Badge } from "@/components/ui/badge";
import { PriceCell } from "@/components/ui/price-cell";
import { formatPercent, formatVolume, formatPrice } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { LivePrice, Stock } from "@/lib/api-types";

interface StockSnapshotProps {
  stock?: Stock;
  livePrice?: LivePrice;
}

export function StockSnapshot({ stock, livePrice }: StockSnapshotProps) {
  const changePct = livePrice?.change_pct ?? 0;
  const change = livePrice?.change ?? 0;

  return (
    <div className="rounded-panel border border-border bg-card p-5">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-text-primary">
              {stock?.symbol ?? "---"}
            </h2>
            <Badge variant={changePct >= 0 ? "bullish" : "bearish"}>
              {formatPercent(changePct)}
            </Badge>
          </div>
          <p className="mt-1 text-sm text-text-secondary">
            {stock?.name ?? "Loading..."}
          </p>
          {stock?.sector && (
            <span className="mt-1 inline-block text-xs text-text-muted">
              {stock.sector}
            </span>
          )}
        </div>
        <div className="text-right">
          <PriceCell
            price={livePrice?.ltp ?? 0}
            className="text-2xl font-bold"
          />
          <div
            className={cn(
              "mt-1 font-mono text-sm",
              change >= 0 ? "text-bullish" : "text-bearish"
            )}
          >
            {change >= 0 ? "+" : ""}
            {formatPrice(change)}
          </div>
        </div>
      </div>

      {livePrice && (
        <div className="mt-4 grid grid-cols-4 gap-4 border-t border-border pt-4">
          {[
            { label: "Open", value: formatPrice(livePrice.open) },
            { label: "High", value: formatPrice(livePrice.high) },
            { label: "Low", value: formatPrice(livePrice.low) },
            { label: "Volume", value: formatVolume(livePrice.volume) },
          ].map((item) => (
            <div key={item.label}>
              <div className="text-[10px] uppercase tracking-wider text-text-muted">
                {item.label}
              </div>
              <div className="mt-0.5 font-mono text-sm text-text-primary">
                {item.value}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
