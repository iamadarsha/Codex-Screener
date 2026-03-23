"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchApiHealth } from "@/lib/api";

export function useApiHealth() {
  return useQuery({
    queryKey: ["apiHealth"],
    queryFn: fetchApiHealth,
    // Poll every 30 s so the banner auto-dismisses once the API recovers
    refetchInterval: 30_000,
    // Never retry — it either responds or it doesn't; retry logic is in fetchApiHealth
    retry: false,
    // Don't show stale data as "ok" for more than 45 s
    staleTime: 45_000,
  });
}
