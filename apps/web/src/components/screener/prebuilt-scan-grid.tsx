"use client";

import { useState } from "react";
import {
  TrendingUp,
  BarChart3,
  Zap,
  ArrowUpRight,
  Target,
  Activity,
  Waves,
  Shield,
  ArrowDownRight,
  Flame,
  GitBranch,
  Signal,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/cn";
import type { PrebuiltScan } from "@/lib/api-types";

const iconMap: Record<string, typeof TrendingUp> = {
  "trending-up": TrendingUp,
  "bar-chart": BarChart3,
  zap: Zap,
  "arrow-up-right": ArrowUpRight,
  target: Target,
  activity: Activity,
  waves: Waves,
  shield: Shield,
  "arrow-down-right": ArrowDownRight,
  flame: Flame,
  "git-branch": GitBranch,
  signal: Signal,
};

const CATEGORIES = [
  "All",
  "Intraday",
  "Swing",
  "Pattern",
  "Volume",
  "Momentum",
  "Breakout",
  "Moving Averages",
];

interface PrebuiltScanGridProps {
  scans: PrebuiltScan[];
  activeScanId?: string | null;
  onRunScan: (scanId: string) => void;
  isLoading?: boolean;
}

export function PrebuiltScanGrid({
  scans,
  activeScanId,
  onRunScan,
  isLoading,
}: PrebuiltScanGridProps) {
  const [activeCategory, setActiveCategory] = useState("All");

  const filtered =
    activeCategory === "All"
      ? scans
      : scans.filter(
          (s) => s.category.toLowerCase() === activeCategory.toLowerCase()
        );

  return (
    <div>
      {/* Category filter pills */}
      <div className="mb-5 flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={cn(
              "rounded-full px-3.5 py-1.5 text-xs font-medium transition",
              activeCategory === cat
                ? "bg-[#7c5cfc] text-white shadow-accent"
                : "border border-[#232d40] bg-[#161d2d] text-[#8b95a8] hover:border-[#7c5cfc]/40 hover:text-white"
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Card grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map((scan) => {
          const Icon = iconMap[scan.icon ?? ""] ?? Zap;
          const isActive = activeScanId === scan.id;

          return (
            <button
              key={scan.id}
              onClick={() => onRunScan(scan.id)}
              disabled={isLoading && isActive}
              className={cn(
                "group relative flex flex-col items-start rounded-xl border p-4 text-left transition-all",
                isActive
                  ? "border-[#7c5cfc] bg-[rgba(124,92,252,0.08)] shadow-glow"
                  : "border-[#232d40] bg-[#161d2d] hover:border-[#7c5cfc]/50 hover:-translate-y-0.5 hover:shadow-lg"
              )}
            >
              <div
                className={cn(
                  "mb-3 rounded-lg p-2.5",
                  isActive
                    ? "bg-[rgba(124,92,252,0.15)] text-[#7c5cfc]"
                    : "bg-[#1c2333] text-[#8b95a8] group-hover:text-white"
                )}
              >
                <Icon className="h-5 w-5" />
              </div>
              <h4 className="mb-1 text-sm font-semibold text-white">
                {scan.name}
              </h4>
              <p className="text-xs leading-relaxed text-[#8b95a8]">
                {scan.description}
              </p>

              <div className="mt-3 flex w-full items-center justify-between">
                <span className="text-[10px] uppercase tracking-wider text-[#5a6478]">
                  {scan.category}
                </span>
                <span
                  className={cn(
                    "rounded-md px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider transition",
                    isActive && !isLoading
                      ? "bg-[#7c5cfc]/20 text-[#7c5cfc]"
                      : "bg-[#1c2333] text-[#5a6478] group-hover:bg-[#7c5cfc] group-hover:text-white"
                  )}
                >
                  {isActive && isLoading ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    "Run"
                  )}
                </span>
              </div>

              {/* Loading bar */}
              {isActive && isLoading && (
                <div className="mt-2 h-0.5 w-full overflow-hidden rounded-full bg-[#232d40]">
                  <div className="h-full w-1/3 animate-pulse rounded-full bg-[#7c5cfc]" />
                </div>
              )}
            </button>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="py-12 text-center text-sm text-[#5a6478]">
          No scans in this category
        </div>
      )}
    </div>
  );
}
