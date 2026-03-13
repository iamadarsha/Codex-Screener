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
                ? "border-accent bg-accent/[0.12] text-accent-hover"
                : "border-border text-text-secondary hover:border-border hover:text-text-primary"
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
