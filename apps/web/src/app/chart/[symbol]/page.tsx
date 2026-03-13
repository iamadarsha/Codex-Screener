"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/app-shell";
import { PageTransition } from "@/components/layout/page-transition";
import { PriceChart } from "@/components/chart/price-chart";
import { TimeframeTabs } from "@/components/chart/timeframe-tabs";
import { IndicatorPills } from "@/components/chart/indicator-pills";
import { StockSnapshot } from "@/components/chart/stock-snapshot";
import { VolumePanel } from "@/components/chart/volume-panel";
import { Skeleton } from "@/components/ui/skeleton";
import { useLivePrices } from "@/hooks/use-live-prices";
import { fetchStock, fetchPriceHistory, fetchIndicators } from "@/lib/api";

export default function ChartPage() {
  const params = useParams();
  const symbol = (params.symbol as string)?.toUpperCase() ?? "RELIANCE";
  const [timeframe, setTimeframe] = useState("daily");
  const [activeIndicators, setActiveIndicators] = useState<string[]>([]);

  const symbols = useMemo(() => [symbol], [symbol]);
  const livePrices = useLivePrices(symbols);
  const livePrice = livePrices[symbol];

  const { data: stock } = useQuery({
    queryKey: ["stock", symbol],
    queryFn: () => fetchStock(symbol),
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ["priceHistory", symbol, timeframe],
    queryFn: () => fetchPriceHistory(symbol, timeframe),
  });

  const { data: indicators } = useQuery({
    queryKey: ["indicators", symbol],
    queryFn: () => fetchIndicators(symbol),
  });

  const toggleIndicator = (ind: string) => {
    setActiveIndicators((prev) =>
      prev.includes(ind) ? prev.filter((i) => i !== ind) : [...prev, ind]
    );
  };

  const candles = history?.candles ?? [];

  return (
    <AppShell>
      <PageTransition>
        <div className="space-y-4">
          {/* Stock Info */}
          <StockSnapshot stock={stock} livePrice={livePrice} />

          {/* Chart Controls */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <TimeframeTabs active={timeframe} onChange={setTimeframe} />
            <IndicatorPills
              active={activeIndicators}
              onToggle={toggleIndicator}
            />
          </div>

          {/* Main Chart */}
          {historyLoading ? (
            <Skeleton className="h-[500px] w-full" />
          ) : (
            <PriceChart candles={candles} />
          )}

          {/* Volume Panel */}
          {candles.length > 0 && <VolumePanel candles={candles} />}

          {/* Indicator Values */}
          {indicators && (
            <div className="rounded-panel border border-border bg-card p-5">
              <h3 className="mb-3 text-sm font-semibold text-text-primary">
                Technical Indicators
              </h3>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
                {[
                  { label: "EMA 20", value: indicators.ema20 },
                  { label: "EMA 50", value: indicators.ema50 },
                  { label: "RSI", value: indicators.rsi },
                  { label: "MACD", value: indicators.macd },
                  { label: "ADX", value: indicators.adx },
                  { label: "ATR", value: indicators.atr },
                ].map((ind) => (
                  <div key={ind.label}>
                    <div className="text-[10px] uppercase tracking-wider text-text-muted">
                      {ind.label}
                    </div>
                    <div className="mt-0.5 font-mono text-sm text-text-primary">
                      {ind.value?.toFixed(2) ?? "-"}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </PageTransition>
    </AppShell>
  );
}
