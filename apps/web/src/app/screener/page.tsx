"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
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
    if (runPrebuilt.isPending) return;
    setActiveScanId(scanId);
    setResult(null);
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
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
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
          </motion.div>

          {/* Custom Scan Builder */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <CustomScanBuilder
              onRun={handleRunCustom}
              isLoading={runCustom.isPending}
            />
          </motion.div>

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
