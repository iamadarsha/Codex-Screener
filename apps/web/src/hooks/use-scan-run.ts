"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  fetchPrebuiltScans,
  runPrebuiltScan,
  runCustomScan,
} from "@/lib/api";
import type { CustomScanRequest, ScanResult } from "@/lib/api-types";
import { MOCK_PREBUILT_SCANS, MOCK_SCAN_RESULTS, MOCK_SCAN_RESULTS_BY_ID } from "@/lib/mock-data";

function withMockFallback(result: ScanResult, scanName: string, scanId?: string): ScanResult {
  if (result.total_matches === 0 || !result.items?.length) {
    const items = (scanId && MOCK_SCAN_RESULTS_BY_ID[scanId]) || MOCK_SCAN_RESULTS;
    return {
      ...result,
      scan_name: scanName || result.scan_name,
      items,
      total_matches: items.length,
      is_demo: true,
    };
  }
  return result;
}

export function usePrebuiltScans() {
  const query = useQuery({
    queryKey: ["prebuiltScans"],
    queryFn: fetchPrebuiltScans,
    staleTime: 60_000 * 5,
    refetchInterval: 30_000,
    retry: 1,
  });
  return {
    ...query,
    data: query.data ?? (query.isError ? MOCK_PREBUILT_SCANS : undefined),
  };
}

export function useRunPrebuiltScan() {
  return useMutation<ScanResult, Error, string>({
    mutationFn: async (scanId: string) => {
      try {
        const result = await runPrebuiltScan(scanId);
        return withMockFallback(result, result.scan_name, scanId);
      } catch {
        const items = MOCK_SCAN_RESULTS_BY_ID[scanId] || MOCK_SCAN_RESULTS;
        return {
          scan_id: scanId,
          scan_name: scanId.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
          total_matches: items.length,
          items,
          is_demo: true,
          run_at: new Date().toISOString(),
        };
      }
    },
  });
}

export function useRunCustomScan() {
  return useMutation<ScanResult, Error, CustomScanRequest>({
    mutationFn: async (req: CustomScanRequest) => {
      try {
        const result = await runCustomScan(req);
        return withMockFallback(result, "Custom Scan");
      } catch {
        return {
          scan_id: "custom",
          scan_name: "Custom Scan",
          total_matches: MOCK_SCAN_RESULTS.length,
          items: MOCK_SCAN_RESULTS,
          is_demo: true,
          run_at: new Date().toISOString(),
        };
      }
    },
  });
}
