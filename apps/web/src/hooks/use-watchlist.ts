"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchWatchlist, addToWatchlist, removeFromWatchlist } from "@/lib/api";
import { DEFAULT_USER_ID } from "@/lib/constants";
import { toast } from "sonner";

export function useWatchlist(userId: string = DEFAULT_USER_ID) {
  return useQuery({
    queryKey: ["watchlist", userId],
    queryFn: () => fetchWatchlist(userId),
    retry: 0,
    staleTime: 30_000,
    gcTime: 60_000,
  });
}

export function useAddToWatchlist(userId: string = DEFAULT_USER_ID) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => addToWatchlist(userId, symbol),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["watchlist", userId] });
      toast.success("Added to watchlist");
    },
    onError: () => {
      toast.error("Failed to add to watchlist");
    },
  });
}

export function useRemoveFromWatchlist(userId: string = DEFAULT_USER_ID) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => removeFromWatchlist(userId, symbol),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["watchlist", userId] });
      toast.success("Removed from watchlist");
    },
    onError: () => {
      toast.error("Failed to remove from watchlist");
    },
  });
}
