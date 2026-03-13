"use client";

import { Clock, Bell } from "lucide-react";
import { cn } from "@/lib/cn";
import { formatDate, formatTime } from "@/lib/format";
import type { Alert } from "@/lib/api-types";

interface HistoryTimelineProps {
  alerts: Alert[];
}

export function HistoryTimeline({ alerts }: HistoryTimelineProps) {
  const triggered = alerts
    .filter((a) => a.triggered_at)
    .sort(
      (a, b) =>
        new Date(b.triggered_at!).getTime() -
        new Date(a.triggered_at!).getTime()
    );

  return (
    <div className="rounded-panel border border-border bg-card p-5">
      <div className="mb-4 flex items-center gap-2">
        <Clock className="h-4 w-4 text-text-secondary" />
        <h3 className="text-sm font-semibold text-text-primary">Alert History</h3>
      </div>

      {triggered.length === 0 && (
        <div className="py-8 text-center text-sm text-text-muted">
          No triggered alerts yet
        </div>
      )}

      <div className="relative space-y-0">
        {triggered.map((alert, idx) => (
          <div key={alert.id} className="relative flex gap-4 pb-6">
            {/* Timeline line */}
            {idx < triggered.length - 1 && (
              <div className="absolute left-[15px] top-8 h-full w-px bg-border" />
            )}

            {/* Dot */}
            <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-bullish/10">
              <Bell className="h-3.5 w-3.5 text-bullish" />
            </div>

            {/* Content */}
            <div className="flex-1 pt-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-semibold text-text-primary">
                  {alert.symbol}
                </span>
                <span className="text-xs text-text-secondary">
                  {alert.condition_type.replace(/_/g, " ")}
                </span>
              </div>
              <div className="mt-0.5 text-xs text-text-muted">
                {alert.operator} {alert.condition_value}
              </div>
              {alert.triggered_at && (
                <div className="mt-1 text-xs text-text-muted">
                  {formatDate(alert.triggered_at)} at{" "}
                  {formatTime(alert.triggered_at)}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
