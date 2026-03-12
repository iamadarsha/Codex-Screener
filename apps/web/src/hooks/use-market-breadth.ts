"use client";

import { useQuery } from "@tanstack/react-query";
import {
  fetchMarketBreadth,
  fetchMarketStatus,
  fetchMarketIndices,
  fetchMarketSectors,
} from "@/lib/api";
import { REFETCH_INTERVAL, LIVE_REFETCH_INTERVAL } from "@/lib/constants";
import { MOCK_BREADTH, MOCK_MARKET_STATUS, MOCK_INDICES } from "@/lib/mock-data";

export function useMarketBreadth() {
  const query = useQuery({
    queryKey: ["marketBreadth"],
    queryFn: fetchMarketBreadth,
    refetchInterval: REFETCH_INTERVAL,
    retry: 1,
  });
  return {
    ...query,
    data: query.data ?? (query.isError ? MOCK_BREADTH : undefined),
  };
}

export function useMarketStatus() {
  const query = useQuery({
    queryKey: ["marketStatus"],
    queryFn: fetchMarketStatus,
    refetchInterval: REFETCH_INTERVAL,
    retry: 1,
  });
  return {
    ...query,
    data: query.data ?? (query.isError ? MOCK_MARKET_STATUS : undefined),
  };
}

export function useMarketIndices() {
  const query = useQuery({
    queryKey: ["marketIndices"],
    queryFn: fetchMarketIndices,
    refetchInterval: LIVE_REFETCH_INTERVAL,
    retry: 1,
  });
  return {
    ...query,
    data: query.data ?? (query.isError ? MOCK_INDICES : undefined),
  };
}

export function useMarketSectors() {
  return useQuery({
    queryKey: ["marketSectors"],
    queryFn: fetchMarketSectors,
    refetchInterval: REFETCH_INTERVAL,
    retry: 1,
  });
}
