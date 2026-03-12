"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Zap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { formatPrice, formatPercent, formatTime } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { ScanResultItem } from "@/lib/api-types";

interface BreakoutFeedProps {
  items: ScanResultItem[];
}

export function BreakoutFeed({ items }: BreakoutFeedProps) {
  const [visibleItems, setVisibleItems] = useState<ScanResultItem[]>([]);

  useEffect(() => {
    setVisibleItems(items.slice(0, 20));
  }, [items]);

  return (
    <div className="rounded-panel border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-[#1E1F28] px-5 py-3">
        <Zap className="h-4 w-4 text-[#FFA502]" />
        <h3 className="text-sm font-semibold text-white">Live Breakout Feed</h3>
        <Badge variant="accent" className="ml-auto">
          {items.length} signals
        </Badge>
      </div>

      <div className="max-h-[400px] overflow-y-auto">
        <AnimatePresence initial={false}>
          {visibleItems.map((item, idx) => (
            <motion.div
              key={`${item.symbol}-${idx}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.2 }}
            >
              <Link
                href={`/chart/${item.symbol}`}
                className={cn(
                  "flex items-center gap-4 px-5 py-3 transition hover:bg-[#22232D]",
                  idx % 2 === 0 ? "bg-transparent" : "bg-[#13141A]/30"
                )}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-semibold text-white">
                      {item.symbol}
                    </span>
                    <span className="text-xs text-[#8B8D9A]">{item.name}</span>
                  </div>
                  <span className="text-xs text-[#5C5D6E]">{item.sector}</span>
                </div>
                <div className="text-right">
                  <div className="font-mono text-sm text-white">
                    {formatPrice(item.ltp)}
                  </div>
                  <div
                    className={cn(
                      "font-mono text-xs",
                      item.change_pct >= 0
                        ? "text-[#00C896]"
                        : "text-[#FF4757]"
                    )}
                  >
                    {formatPercent(item.change_pct)}
                  </div>
                </div>
                {item.triggered_at && (
                  <span className="text-xs text-[#5C5D6E]">
                    {formatTime(item.triggered_at)}
                  </span>
                )}
              </Link>
            </motion.div>
          ))}
        </AnimatePresence>
        {visibleItems.length === 0 && (
          <div className="px-5 py-12 text-center text-sm text-[#5C5D6E]">
            No breakout signals yet
          </div>
        )}
      </div>
    </div>
  );
}
