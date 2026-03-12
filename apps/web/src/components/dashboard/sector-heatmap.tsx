"use client";

import { cn } from "@/lib/cn";
import { formatPercent } from "@/lib/format";
import type { SectorData } from "@/lib/api-types";

interface SectorHeatmapProps {
  sectors: SectorData[];
}

function getHeatColor(changePct: number): string {
  if (changePct >= 3) return "bg-[#00897B]";
  if (changePct >= 1) return "bg-[#00C896]";
  if (changePct >= 0) return "bg-[#00C896]/40";
  if (changePct >= -1) return "bg-[#FF4757]/40";
  if (changePct >= -3) return "bg-[#FF4757]";
  return "bg-[#D32F2F]";
}

function getTextColor(changePct: number): string {
  if (Math.abs(changePct) >= 1) return "text-white";
  return "text-[#E8E9F0]";
}

export function SectorHeatmap({ sectors }: SectorHeatmapProps) {
  return (
    <div className="rounded-panel border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-semibold text-white">
        Sector Performance
      </h3>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        {sectors.map((sector) => (
          <div
            key={sector.sector}
            className={cn(
              "flex flex-col items-center justify-center rounded-lg px-3 py-4 transition hover:opacity-90",
              getHeatColor(sector.change_pct)
            )}
          >
            <span
              className={cn(
                "text-xs font-semibold",
                getTextColor(sector.change_pct)
              )}
            >
              {sector.sector}
            </span>
            <span
              className={cn(
                "mt-1 font-mono text-lg font-bold",
                getTextColor(sector.change_pct)
              )}
            >
              {formatPercent(sector.change_pct, 1)}
            </span>
            <div className="mt-1.5 flex gap-2 text-[10px]">
              <span className="text-[#00C896]">{sector.advances}A</span>
              <span className="text-[#FF4757]">{sector.declines}D</span>
            </div>
          </div>
        ))}
      </div>

      {sectors.length === 0 && (
        <div className="py-12 text-center text-sm text-[#5C5D6E]">
          No sector data available
        </div>
      )}
    </div>
  );
}
