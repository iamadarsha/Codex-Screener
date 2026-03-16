"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  fetchPrebuiltScans,
  runPrebuiltScan,
  runCustomScan,
} from "@/lib/api";
import type { CustomScanRequest, ScanResult } from "@/lib/api-types";
import { PREBUILT_SCAN_DEFINITIONS } from "@/lib/mock-data";

export function usePrebuiltScans() {
  return useQuery({
    queryKey: ["prebuiltScans"],
    queryFn: async () => {
      try {
        const scans = await fetchPrebuiltScans();
        return scans && scans.length > 0 ? scans : PREBUILT_SCAN_DEFINITIONS;
      } catch {
        return PREBUILT_SCAN_DEFINITIONS;
      }
    },
    staleTime: 60_000 * 5,
    refetchInterval: 60_000,
    retry: 0,
    placeholderData: PREBUILT_SCAN_DEFINITIONS,
  });
}

const EMPTY_RESULT = (scanId: string, scanName: string): ScanResult => ({
  scan_id: scanId,
  scan_name: scanName,
  total_matches: 0,
  items: [],
  run_at: new Date().toISOString(),
});

export function useRunPrebuiltScan() {
  return useMutation<ScanResult, Error, string>({
    mutationFn: async (scanId: string) => {
      try {
        return await runPrebuiltScan(scanId);
      } catch {
        return EMPTY_RESULT(
          scanId,
          scanId.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
        );
      }
    },
  });
}

export function useRunCustomScan() {
  return useMutation<ScanResult, Error, CustomScanRequest>({
    mutationFn: async (req: CustomScanRequest) => {
      try {
        return await runCustomScan(req);
      } catch {
        return EMPTY_RESULT("custom", "Custom Scan");
      }
    },
  });
}
