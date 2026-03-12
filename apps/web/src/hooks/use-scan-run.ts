"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  fetchPrebuiltScans,
  runPrebuiltScan,
  runCustomScan,
} from "@/lib/api";
import type { CustomScanRequest, ScanResult } from "@/lib/api-types";
import { MOCK_PREBUILT_SCANS } from "@/lib/mock-data";

export function usePrebuiltScans() {
  const query = useQuery({
    queryKey: ["prebuiltScans"],
    queryFn: fetchPrebuiltScans,
    staleTime: 60_000 * 5,
    retry: 1,
  });
  return {
    ...query,
    data: query.data ?? (query.isError ? MOCK_PREBUILT_SCANS : undefined),
  };
}

export function useRunPrebuiltScan() {
  return useMutation<ScanResult, Error, string>({
    mutationFn: (scanId: string) => runPrebuiltScan(scanId),
  });
}

export function useRunCustomScan() {
  return useMutation<ScanResult, Error, CustomScanRequest>({
    mutationFn: (req: CustomScanRequest) => runCustomScan(req),
  });
}
