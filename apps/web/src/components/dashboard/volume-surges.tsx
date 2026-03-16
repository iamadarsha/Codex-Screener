"use client";

import Link from "next/link";
import { BarChart3 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { formatPrice, formatPercent, formatVolume } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { ScanResultItem } from "@/lib/api-types";

interface VolumeSurgesProps {
  items: ScanResultItem[];
}

export function VolumeSurges({ items }: VolumeSurgesProps) {
  return (
    <div className="rounded-panel border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-[#1E1F28] px-5 py-3">
        <BarChart3 className="h-4 w-4 text-[#FFA502]" />
        <h3 className="text-sm font-semibold text-white">Volume Surges</h3>
        <Badge variant="warning" className="ml-auto">
          {items.length}
        </Badge>
      </div>

      <div className="max-h-[350px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#1E1F28] text-xs uppercase tracking-wider text-[#8B8D9A]">
              <th className="px-5 py-2.5 text-left">Symbol</th>
              <th className="px-5 py-2.5 text-right">LTP</th>
              <th className="px-5 py-2.5 text-right">Change</th>
              <th className="px-5 py-2.5 text-right">Volume</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => (
              <tr
                key={item.symbol}
                className={cn(
                  "transition hover:bg-[#22232D]",
                  idx % 2 === 0 ? "bg-transparent" : "bg-[#13141A]/30"
                )}
              >
                <td className="px-5 py-2.5">
                  <Link
                    href={`/chart/${item.symbol}`}
                    className="font-mono font-semibold text-white hover:text-[#7C5CFC]"
                  >
                    {item.symbol}
                  </Link>
                </td>
                <td className="px-5 py-2.5 text-right font-mono text-white">
                  {formatPrice(item.ltp ?? 0)}
                </td>
                <td
                  className={cn(
                    "px-5 py-2.5 text-right font-mono",
                    (item.change_pct ?? 0) >= 0
                      ? "text-[#00C896]"
                      : "text-[#FF4757]"
                  )}
                >
                  {formatPercent(item.change_pct ?? 0)}
                </td>
                <td className="px-5 py-2.5 text-right font-mono text-[#FFA502]">
                  {formatVolume(item.volume ?? 0)}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-12 text-center text-[#5C5D6E]">
                  No volume surges detected
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
