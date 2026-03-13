"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/cn";

interface CountdownBarProps {
  /** Market open time as HH:mm (IST) */
  openTime?: string;
  /** Market close time as HH:mm (IST) */
  closeTime?: string;
  isOpen: boolean;
  className?: string;
}

function getMinutesSinceMidnight(): number {
  const now = new Date();
  return now.getHours() * 60 + now.getMinutes();
}

function parseTime(t: string): number {
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
}

export function CountdownBar({
  openTime = "09:15",
  closeTime = "15:30",
  isOpen,
  className,
}: CountdownBarProps) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const update = () => {
      const now = getMinutesSinceMidnight();
      const open = parseTime(openTime);
      const close = parseTime(closeTime);
      const total = close - open;
      if (total <= 0) {
        setProgress(0);
        return;
      }
      const elapsed = now - open;
      setProgress(Math.max(0, Math.min(1, elapsed / total)));
    };

    update();
    const interval = setInterval(update, 30_000);
    return () => clearInterval(interval);
  }, [openTime, closeTime]);

  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div className="flex items-center justify-between text-[10px] text-text-secondary">
        <span>{openTime} IST</span>
        <span className={isOpen ? "text-bullish" : "text-bearish"}>
          {isOpen ? "Market Open" : "Market Closed"}
        </span>
        <span>{closeTime} IST</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent to-bullish transition-all duration-500"
          style={{ width: `${isOpen ? progress * 100 : 0}%` }}
        />
      </div>
    </div>
  );
}
