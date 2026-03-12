"use client";

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
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {scans.map((scan) => {
        const Icon = iconMap[scan.icon ?? ""] ?? Zap;
        const isActive = activeScanId === scan.id;

        return (
          <button
            key={scan.id}
            onClick={() => onRunScan(scan.id)}
            disabled={isLoading && isActive}
            className={cn(
              "group flex flex-col items-start rounded-xl border p-4 text-left transition",
              isActive
                ? "border-[#7C5CFC] bg-[rgba(124,92,252,0.08)]"
                : "border-[#2A2B35] bg-card hover:border-[#3A3B45] hover:-translate-y-0.5"
            )}
          >
            <div
              className={cn(
                "mb-3 rounded-lg p-2",
                isActive
                  ? "bg-[rgba(124,92,252,0.15)] text-[#7C5CFC]"
                  : "bg-[#22232D] text-[#8B8D9A] group-hover:text-white"
              )}
            >
              <Icon className="h-5 w-5" />
            </div>
            <h4 className="mb-1 text-sm font-semibold text-white">
              {scan.name}
            </h4>
            <p className="text-xs leading-relaxed text-[#8B8D9A]">
              {scan.description}
            </p>
            <span className="mt-2 text-[10px] uppercase tracking-wider text-[#5C5D6E]">
              {scan.category}
            </span>
            {isActive && isLoading && (
              <div className="mt-2 h-0.5 w-full overflow-hidden rounded-full bg-[#2A2B35]">
                <div className="h-full w-1/3 animate-pulse rounded-full bg-[#7C5CFC]" />
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
