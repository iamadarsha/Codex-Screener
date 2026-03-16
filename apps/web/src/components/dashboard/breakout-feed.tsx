"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Zap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { SignalBadge } from "@/components/shared/signal-badge";
import { formatPrice, formatPercent } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { ScanResultItem } from "@/lib/api-types";

function timeAgo(dateStr?: string): string {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function FlashPrice({ price }: { price: number }) {
  const prevRef = useRef(price);
  const [flash, setFlash] = useState<string | null>(null);

  useEffect(() => {
    if (price > prevRef.current) setFlash("flash-bullish");
    else if (price < prevRef.current) setFlash("flash-bearish");
    prevRef.current = price;
    const t = setTimeout(() => setFlash(null), 600);
    return () => clearTimeout(t);
  }, [price]);

  return (
    <span
      className={cn(
        "inline-block rounded px-1 font-mono text-sm tabular-nums text-text-primary",
        flash
      )}
    >
      {formatPrice(price)}
    </span>
  );
}

interface BreakoutFeedProps {
  items: ScanResultItem[];
}

export function BreakoutFeed({ items }: BreakoutFeedProps) {
  const [visibleItems, setVisibleItems] = useState<ScanResultItem[]>([]);

  useEffect(() => {
    setVisibleItems(items.slice(0, 20));
  }, [items]);

  return (
    <div className="glass-card rounded-panel overflow-hidden">
      <div className="flex items-center gap-2 border-b border-border px-3 py-3 sm:px-5">
        <Zap className="h-4 w-4 text-warning" />
        <h3 className="text-sm font-semibold text-text-primary">Live Breakout Feed</h3>
        <Badge variant="accent" className="ml-auto">
          {items.length} signals
        </Badge>
      </div>

      <div className="max-h-[420px] overflow-y-auto">
        <AnimatePresence initial={false}>
          {visibleItems.map((item, idx) => (
            <motion.div
              key={`${item.symbol}-${idx}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 16 }}
              transition={{ delay: idx * 0.05, duration: 0.25, ease: "easeOut" }}
            >
              <Link
                href={`/chart/${item.symbol}`}
                className={cn(
                  "flex items-center gap-2 px-3 py-3 transition hover:bg-elevated sm:gap-4 sm:px-5",
                  idx % 2 === 0 ? "bg-transparent" : "bg-sidebar/30"
                )}
              >
                {/* Symbol & name */}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-semibold text-text-primary">
                      {item.symbol}
                    </span>
                    <span className="truncate text-xs text-text-secondary">
                      {item.company_name ?? item.name}
                    </span>
                  </div>
                  <div className="mt-0.5 flex items-center gap-2">
                    <span className="text-[11px] text-text-muted">{item.sector}</span>
                    {item.signal_strength != null && (
                      <SignalBadge
                        signal={
                          item.signal_strength > 80
                            ? "BREAKOUT"
                            : item.signal_strength > 60
                              ? "VOLUME"
                              : "EMA"
                        }
                      />
                    )}
                  </div>
                </div>

                {/* Price & change */}
                <div className="text-right">
                  <FlashPrice price={item.ltp} />
                  <div
                    className={cn(
                      "font-mono text-xs tabular-nums",
                      item.change_pct >= 0 ? "text-bullish" : "text-bearish"
                    )}
                  >
                    {formatPercent(item.change_pct)}
                  </div>
                </div>

                {/* Time ago */}
                {item.triggered_at && (
                  <span className="shrink-0 text-[10px] text-text-muted">
                    {timeAgo(item.triggered_at)}
                  </span>
                )}
              </Link>
            </motion.div>
          ))}
        </AnimatePresence>
        {visibleItems.length === 0 && (
          <div className="px-5 py-12 text-center text-sm text-text-muted">
            No breakout signals yet
          </div>
        )}
      </div>
    </div>
  );
}
