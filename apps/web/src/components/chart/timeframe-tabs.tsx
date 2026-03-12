"use client";

import { TIMEFRAME_OPTIONS } from "@/lib/constants";
import { cn } from "@/lib/cn";

interface TimeframeTabsProps {
  active: string;
  onChange: (tf: string) => void;
}

export function TimeframeTabs({ active, onChange }: TimeframeTabsProps) {
  return (
    <div className="flex items-center gap-1 rounded-lg border border-[#2A2B35] bg-[#13141A] p-1">
      {TIMEFRAME_OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={cn(
            "rounded-md px-3 py-1.5 text-xs font-semibold transition",
            active === opt.value
              ? "bg-[#7C5CFC] text-white"
              : "text-[#8B8D9A] hover:text-white"
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
