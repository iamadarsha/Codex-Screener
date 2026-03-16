"use client";

import { useQuery } from "@tanstack/react-query";
import {
  fetchMarketBreadth,
  fetchMarketStatus,
  fetchMarketIndices,
  fetchMarketSectors,
} from "@/lib/api";

export function useMarketBreadth() {
  return useQuery({
    queryKey: ["marketBreadth"],
    queryFn: fetchMarketBreadth,
    refetchInterval: 30_000,
    staleTime: 20_000,
    retry: 1,
  });
}

export function useMarketStatus() {
  return useQuery({
    queryKey: ["marketStatus"],
    queryFn: fetchMarketStatus,
    refetchInterval: 60_000,
    staleTime: 30_000,
    retry: 1,
  });
}

export function useMarketIndices() {
  return useQuery({
    queryKey: ["marketIndices"],
    queryFn: fetchMarketIndices,
    refetchInterval: 30_000,
    staleTime: 20_000,
    retry: 1,
  });
}

export function useMarketSectors() {
  return useQuery({
    queryKey: ["marketSectors"],
    queryFn: fetchMarketSectors,
    refetchInterval: 60_000,
    staleTime: 30_000,
    retry: 1,
  });
}
