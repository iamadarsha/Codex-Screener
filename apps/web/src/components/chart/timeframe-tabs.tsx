"use client";

import { TIMEFRAME_OPTIONS } from "@/lib/constants";
import { cn } from "@/lib/cn";

interface TimeframeTabsProps {
  active: string;
  onChange: (tf: string) => void;
}

export function TimeframeTabs({ active, onChange }: TimeframeTabsProps) {
  return (
    <div className="flex items-center gap-1 rounded-lg border border-border bg-page p-1">
      {TIMEFRAME_OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={cn(
            "rounded-md px-3 py-1.5 text-xs font-semibold transition",
            active === opt.value
              ? "bg-accent text-white"
              : "text-text-secondary hover:text-text-primary"
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
