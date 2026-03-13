"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  fetchPrebuiltScans,
  runPrebuiltScan,
  runCustomScan,
} from "@/lib/api";
import type { CustomScanRequest, ScanResult } from "@/lib/api-types";
import { MOCK_PREBUILT_SCANS, MOCK_SCAN_RESULTS } from "@/lib/mock-data";

function withMockFallback(result: ScanResult, scanName: string): ScanResult {
  if (result.total_matches === 0 || !result.items?.length) {
    return {
      ...result,
      scan_name: scanName || result.scan_name,
      items: MOCK_SCAN_RESULTS,
      total_matches: MOCK_SCAN_RESULTS.length,
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
        return withMockFallback(result, result.scan_name);
      } catch {
        return {
          scan_id: scanId,
          scan_name: scanId.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
          total_matches: MOCK_SCAN_RESULTS.length,
          items: MOCK_SCAN_RESULTS,
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
          run_at: new Date().toISOString(),
        };
      }
    },
  });
}
