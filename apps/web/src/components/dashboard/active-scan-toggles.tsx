"use client";

import { useState } from "react";
import { Play, Pause } from "lucide-react";
import { cn } from "@/lib/cn";
import type { PrebuiltScan } from "@/lib/api-types";

interface ActiveScanTogglesProps {
  scans: PrebuiltScan[];
  onRunScan: (scanId: string) => void;
}

export function ActiveScanToggles({ scans, onRunScan }: ActiveScanTogglesProps) {
  const [activeScans, setActiveScans] = useState<Set<string>>(new Set());

  const toggleScan = (scanId: string) => {
    setActiveScans((prev) => {
      const next = new Set(prev);
      if (next.has(scanId)) {
        next.delete(scanId);
      } else {
        next.add(scanId);
        onRunScan(scanId);
      }
      return next;
    });
  };

  return (
    <div className="rounded-panel border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-semibold text-white">Active Scans</h3>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {scans.slice(0, 6).map((scan) => {
          const isActive = activeScans.has(scan.id);
          return (
            <button
              key={scan.id}
              onClick={() => toggleScan(scan.id)}
              className={cn(
                "flex items-center gap-2 rounded-lg border px-3 py-2.5 text-left text-sm transition",
                isActive
                  ? "border-[#7C5CFC] bg-[rgba(124,92,252,0.1)] text-white"
                  : "border-[#2A2B35] bg-[#13141A] text-[#8B8D9A] hover:border-[#3A3B45] hover:text-white"
              )}
            >
              {isActive ? (
                <Pause className="h-3.5 w-3.5 shrink-0 text-[#7C5CFC]" />
              ) : (
                <Play className="h-3.5 w-3.5 shrink-0" />
              )}
              <span className="truncate text-xs">{scan.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
