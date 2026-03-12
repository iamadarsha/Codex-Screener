"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { PageTransition } from "@/components/layout/page-transition";
import { StatCards } from "@/components/dashboard/stat-cards";
import { BreakoutFeed } from "@/components/dashboard/breakout-feed";
import { BreadthDonut } from "@/components/dashboard/breadth-donut";
import { VolumeSurges } from "@/components/dashboard/volume-surges";
import { SectorHeatmap } from "@/components/dashboard/sector-heatmap";
import { ActiveScanToggles } from "@/components/dashboard/active-scan-toggles";
import { SectionHeading } from "@/components/ui/section-heading";
import { SkeletonCard } from "@/components/ui/skeleton";
import { useMarketBreadth, useMarketSectors } from "@/hooks/use-market-breadth";
import { usePrebuiltScans, useRunPrebuiltScan } from "@/hooks/use-scan-run";
import type { ScanResultItem } from "@/lib/api-types";

export default function DashboardPage() {
  const { data: breadth, isLoading: breadthLoading } = useMarketBreadth();
  const { data: sectors } = useMarketSectors();
  const { data: scans } = usePrebuiltScans();
  const runScan = useRunPrebuiltScan();

  const [breakoutItems, setBreakoutItems] = useState<ScanResultItem[]>([]);
  const [volumeItems, setVolumeItems] = useState<ScanResultItem[]>([]);

  const handleRunScan = useCallback(
    (scanId: string) => {
      runScan.mutate(scanId, {
        onSuccess: (result) => {
          setBreakoutItems((prev) => {
            const newItems = result.results.filter(
              (r) => !prev.some((p) => p.symbol === r.symbol)
            );
            return [...newItems, ...prev].slice(0, 50);
          });
          // Volume surges from any scan with high volume
          const volSurges = result.results.filter((r) => r.volume > 0);
          if (volSurges.length > 0) {
            setVolumeItems((prev) => {
              const combined = [...volSurges, ...prev];
              const unique = combined.filter(
                (item, idx) =>
                  combined.findIndex((i) => i.symbol === item.symbol) === idx
              );
              return unique.slice(0, 20);
            });
          }
        },
      });
    },
    [runScan]
  );

  // Auto-run a default scan on mount
  useEffect(() => {
    if (scans && scans.length > 0 && breakoutItems.length === 0) {
      handleRunScan(scans[0].id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scans]);

  const alertCount = useMemo(
    () => breakoutItems.filter((i) => i.signal_strength && i.signal_strength > 0.7).length,
    [breakoutItems]
  );

  return (
    <AppShell>
      <PageTransition>
        <div className="space-y-6">
          <SectionHeading
            title="Dashboard"
            subtitle="Real-time market overview and breakout signals"
          />

          {/* Stat Cards */}
          {breadthLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : (
            <StatCards
              breakoutCount={breakoutItems.length}
              alertCount={alertCount}
              volumeSurgeCount={volumeItems.length}
              breadth={breadth}
            />
          )}

          {/* Main Grid */}
          <div className="grid gap-6 xl:grid-cols-3">
            {/* Left: Breakout Feed */}
            <div className="xl:col-span-2 space-y-6">
              <BreakoutFeed items={breakoutItems} />
              <VolumeSurges items={volumeItems} />
            </div>

            {/* Right: Breadth + Scan Toggles */}
            <div className="space-y-6">
              <BreadthDonut breadth={breadth} />
              {scans && (
                <ActiveScanToggles
                  scans={scans}
                  onRunScan={handleRunScan}
                />
              )}
            </div>
          </div>

          {/* Sector Heatmap */}
          {sectors && <SectorHeatmap sectors={sectors} />}
        </div>
      </PageTransition>
    </AppShell>
  );
}
