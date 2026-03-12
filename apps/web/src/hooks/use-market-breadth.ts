"use client";

import { useQuery } from "@tanstack/react-query";
import {
  fetchMarketBreadth,
  fetchMarketStatus,
  fetchMarketIndices,
  fetchMarketSectors,
} from "@/lib/api";
import { REFETCH_INTERVAL, LIVE_REFETCH_INTERVAL } from "@/lib/constants";

export function useMarketBreadth() {
  return useQuery({
    queryKey: ["marketBreadth"],
    queryFn: fetchMarketBreadth,
    refetchInterval: REFETCH_INTERVAL,
  });
}

export function useMarketStatus() {
  return useQuery({
    queryKey: ["marketStatus"],
    queryFn: fetchMarketStatus,
    refetchInterval: REFETCH_INTERVAL,
  });
}

export function useMarketIndices() {
  return useQuery({
    queryKey: ["marketIndices"],
    queryFn: fetchMarketIndices,
    refetchInterval: LIVE_REFETCH_INTERVAL,
  });
}

export function useMarketSectors() {
  return useQuery({
    queryKey: ["marketSectors"],
    queryFn: fetchMarketSectors,
    refetchInterval: REFETCH_INTERVAL,
  });
}
