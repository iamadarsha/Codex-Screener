"use client";

import { cn } from "@/lib/cn";
import { formatPercent } from "@/lib/format";
import type { SectorData } from "@/lib/api-types";

interface SectorHeatmapProps {
  sectors: SectorData[];
}

function getHeatBg(changePct: number): string {
  if (changePct >= 3) return "bg-[#00897B]";
  if (changePct >= 2) return "bg-[#00a88a]";
  if (changePct >= 1) return "bg-bullish/80";
  if (changePct >= 0.25) return "bg-bullish/40";
  if (changePct >= -0.25) return "bg-border";
  if (changePct >= -1) return "bg-bearish/40";
  if (changePct >= -2) return "bg-bearish/70";
  if (changePct >= -3) return "bg-[#e0436e]";
  return "bg-[#c62c55]";
}

function getTextColor(changePct: number): string {
  if (Math.abs(changePct) >= 0.25) return "text-white";
  return "text-text-primary";
}

export function SectorHeatmap({ sectors }: SectorHeatmapProps) {
  return (
    <div className="glass-card rounded-panel p-5">
      <h3 className="mb-4 text-sm font-semibold text-text-primary">
        Sector Performance
      </h3>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        {sectors.map((sector) => (
          <div
            key={sector.sector}
            className={cn(
              "group relative flex flex-col items-center justify-center rounded-lg px-3 py-4 transition-all hover:scale-[1.02] hover:shadow-lg",
              getHeatBg(sector.change_pct)
            )}
          >
            <span
              className={cn(
                "text-[11px] font-semibold leading-tight text-center",
                getTextColor(sector.change_pct)
              )}
            >
              {sector.sector}
            </span>
            <span
              className={cn(
                "mt-1.5 font-mono text-lg font-bold tabular-nums",
                getTextColor(sector.change_pct)
              )}
            >
              {formatPercent(sector.change_pct, 1)}
            </span>
            <div className="mt-2 flex gap-3 text-[10px]">
              <span className="text-bullish">
                <span className="opacity-60">A</span> {sector.advances}
              </span>
              <span className="text-bearish">
                <span className="opacity-60">D</span> {sector.declines}
              </span>
            </div>

            {/* Hover tooltip with top gainer/loser */}
            <div className="pointer-events-none absolute -bottom-1 left-1/2 z-10 -translate-x-1/2 translate-y-full scale-95 rounded-lg border border-border bg-elevated px-3 py-2 opacity-0 shadow-lg transition group-hover:scale-100 group-hover:opacity-100">
              <div className="whitespace-nowrap text-[10px]">
                <span className="text-bullish">+{sector.top_gainer}</span>
                {" / "}
                <span className="text-bearish">-{sector.top_loser}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {sectors.length === 0 && (
        <div className="py-12 text-center text-sm text-text-muted">
          No sector data available
        </div>
      )}
    </div>
  );
}
