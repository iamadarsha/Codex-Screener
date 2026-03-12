"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  fetchPrebuiltScans,
  runPrebuiltScan,
  runCustomScan,
} from "@/lib/api";
import type { CustomScanRequest, ScanResult } from "@/lib/api-types";

export function usePrebuiltScans() {
  return useQuery({
    queryKey: ["prebuiltScans"],
    queryFn: fetchPrebuiltScans,
    staleTime: 60_000 * 5,
  });
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
