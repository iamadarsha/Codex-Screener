"use client";

import { Bell, BellOff, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";
import { formatDate } from "@/lib/format";
import type { Alert } from "@/lib/api-types";

interface ActiveAlertsListProps {
  alerts: Alert[];
}

export function ActiveAlertsList({ alerts }: ActiveAlertsListProps) {
  const activeAlerts = alerts.filter((a) => a.is_active);
  const triggeredAlerts = alerts.filter((a) => !a.is_active && a.triggered_at);

  return (
    <div className="rounded-panel border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border px-5 py-3">
        <Bell className="h-4 w-4 text-accent" />
        <h3 className="text-sm font-semibold text-text-primary">Active Alerts</h3>
        <Badge variant="accent" className="ml-auto">
          {activeAlerts.length} active
        </Badge>
      </div>

      <div className="max-h-[400px] overflow-y-auto">
        {activeAlerts.length === 0 && triggeredAlerts.length === 0 && (
          <div className="px-5 py-12 text-center text-sm text-text-muted">
            No alerts created yet
          </div>
        )}

        {activeAlerts.map((alert) => (
          <div
            key={alert.id}
            className="flex items-center gap-4 border-b border-border px-5 py-3 transition hover:bg-elevated"
          >
            <div className="rounded-lg bg-accent/10 p-2">
              <Bell className="h-4 w-4 text-accent" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-semibold text-text-primary">
                  {alert.symbol}
                </span>
                <Badge variant="accent">Active</Badge>
              </div>
              <div className="mt-0.5 text-xs text-text-secondary">
                {alert.condition_type.replace(/_/g, " ")} {alert.operator}{" "}
                <span className="font-mono">{alert.condition_value}</span>
              </div>
            </div>
            <span className="text-xs text-text-muted">
              {formatDate(alert.created_at)}
            </span>
          </div>
        ))}

        {triggeredAlerts.length > 0 && (
          <>
            <div className="flex items-center gap-2 border-b border-border bg-page/50 px-5 py-2">
              <BellOff className="h-3.5 w-3.5 text-text-muted" />
              <span className="text-xs font-medium text-text-muted">
                Recently Triggered
              </span>
            </div>
            {triggeredAlerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className="flex items-center gap-4 border-b border-border px-5 py-3 opacity-60"
              >
                <div className="rounded-lg bg-bullish/10 p-2">
                  <Bell className="h-4 w-4 text-bullish" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm text-text-primary">
                      {alert.symbol}
                    </span>
                    <Badge variant="bullish">Triggered</Badge>
                  </div>
                  <div className="mt-0.5 text-xs text-text-secondary">
                    {alert.condition_type.replace(/_/g, " ")} {alert.operator}{" "}
                    <span className="font-mono">{alert.condition_value}</span>
                  </div>
                </div>
                {alert.triggered_at && (
                  <span className="text-xs text-text-muted">
                    {formatDate(alert.triggered_at)}
                  </span>
                )}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
