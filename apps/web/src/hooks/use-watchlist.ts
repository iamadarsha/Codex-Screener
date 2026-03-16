"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchWatchlist, addToWatchlist, removeFromWatchlist } from "@/lib/api";
import { toast } from "sonner";

export function useWatchlist() {
  return useQuery({
    queryKey: ["watchlist"],
    queryFn: () => fetchWatchlist(),
    retry: 0,
    staleTime: 30_000,
    gcTime: 60_000,
  });
}

export function useAddToWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => addToWatchlist(symbol),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["watchlist"] });
      toast.success("Added to watchlist");
    },
    onError: () => {
      toast.error("Failed to add to watchlist");
    },
  });
}

export function useRemoveFromWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => removeFromWatchlist(symbol),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["watchlist"] });
      toast.success("Removed from watchlist");
    },
    onError: () => {
      toast.error("Failed to remove from watchlist");
    },
  });
}
