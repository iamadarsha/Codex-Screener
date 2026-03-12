"use client";

import { INDICATOR_OPTIONS } from "@/lib/constants";
import { cn } from "@/lib/cn";

interface IndicatorPillsProps {
  active: string[];
  onToggle: (indicator: string) => void;
}

export function IndicatorPills({ active, onToggle }: IndicatorPillsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {INDICATOR_OPTIONS.map((opt) => {
        const isActive = active.includes(opt.value);
        return (
          <button
            key={opt.value}
            onClick={() => onToggle(opt.value)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition",
              isActive
                ? "border-[#7C5CFC] bg-[rgba(124,92,252,0.12)] text-[#9B7FFF]"
                : "border-[#2A2B35] text-[#8B8D9A] hover:border-[#3A3B45] hover:text-white"
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
