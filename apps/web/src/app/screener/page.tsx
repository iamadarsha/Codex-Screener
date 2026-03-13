"use client";

import { useState } from "react";
import { AnimatePresence } from "framer-motion";
import { AppShell } from "@/components/layout/app-shell";
import { PageTransition } from "@/components/layout/page-transition";
import { SectionHeading } from "@/components/ui/section-heading";
import { PrebuiltScanGrid } from "@/components/screener/prebuilt-scan-grid";
import { ScanResultsPanel } from "@/components/screener/scan-results-panel";
import { CustomScanBuilder } from "@/components/screener/custom-scan-builder";
import { SkeletonTable } from "@/components/ui/skeleton";
import {
  usePrebuiltScans,
  useRunPrebuiltScan,
  useRunCustomScan,
} from "@/hooks/use-scan-run";
import type { ScanResult, CustomScanCondition } from "@/lib/api-types";

export default function ScreenerPage() {
  const { data: scans, isLoading: scansLoading } = usePrebuiltScans();
  const runPrebuilt = useRunPrebuiltScan();
  const runCustom = useRunCustomScan();
  const [activeScanId, setActiveScanId] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);

  const handleRunPrebuilt = (scanId: string) => {
    setActiveScanId(scanId);
    runPrebuilt.mutate(scanId, {
      onSuccess: (data) => setResult(data),
    });
  };

  const handleRunCustom = (
    conditions: CustomScanCondition[],
    universe: string,
    timeframe: string
  ) => {
    setActiveScanId("custom");
    runCustom.mutate(
      { conditions, universe, timeframe },
      {
        onSuccess: (data) => setResult(data),
      }
    );
  };

  return (
    <AppShell>
      <PageTransition>
        <div className="space-y-6">
          <SectionHeading
            title="Screener"
            subtitle="Run prebuilt scans or build your own custom conditions"
          />

          {/* Prebuilt Scans Grid */}
          <div>
            <h3 className="mb-3 text-sm font-semibold text-text-secondary">
              Prebuilt Scans
            </h3>
            {scansLoading ? (
              <SkeletonTable rows={3} />
            ) : (
              <PrebuiltScanGrid
                scans={scans ?? []}
                activeScanId={activeScanId}
                onRunScan={handleRunPrebuilt}
                isLoading={runPrebuilt.isPending}
              />
            )}
          </div>

          {/* Custom Scan Builder */}
          <CustomScanBuilder
            onRun={handleRunCustom}
            isLoading={runCustom.isPending}
          />

          {/* Results */}
          <AnimatePresence>
            {result && (
              <ScanResultsPanel
                result={result}
                onClose={() => {
                  setResult(null);
                  setActiveScanId(null);
                }}
              />
            )}
          </AnimatePresence>
        </div>
      </PageTransition>
    </AppShell>
  );
}
