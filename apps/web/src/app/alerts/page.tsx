"use client";

import { AppShell } from "@/components/layout/app-shell";
import { PageTransition } from "@/components/layout/page-transition";
import { SectionHeading } from "@/components/ui/section-heading";
import { SkeletonCard } from "@/components/ui/skeleton";
import { AlertForm } from "@/components/alerts/alert-form";
import { ActiveAlertsList } from "@/components/alerts/active-alerts-list";
import { HistoryTimeline } from "@/components/alerts/history-timeline";
import { useAlerts, useCreateAlert } from "@/hooks/use-alerts";

export default function AlertsPage() {
  const { data: alerts, isLoading } = useAlerts();
  const createMutation = useCreateAlert();

  return (
    <AppShell>
      <PageTransition>
        <div className="space-y-6">
          <SectionHeading
            title="Alerts"
            subtitle="Set price and indicator alerts for your stocks"
          />

          <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
            {/* Alert Form */}
            <AlertForm
              onSubmit={(req) => createMutation.mutate(req)}
              isLoading={createMutation.isPending}
            />

            {/* Active Alerts + History */}
            <div className="space-y-6">
              {isLoading ? (
                <>
                  <SkeletonCard />
                  <SkeletonCard />
                </>
              ) : (
                <>
                  <ActiveAlertsList alerts={alerts ?? []} />
                  <HistoryTimeline alerts={alerts ?? []} />
                </>
              )}
            </div>
          </div>
        </div>
      </PageTransition>
    </AppShell>
  );
}
