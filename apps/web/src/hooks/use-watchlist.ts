"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchWatchlist, addToWatchlist, removeFromWatchlist } from "@/lib/api";
import { toast } from "sonner";
import { haptic } from "@/lib/haptic";

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
      haptic("medium");
      qc.invalidateQueries({ queryKey: ["watchlist"] });
      toast.success("Added to watchlist");
    },
    onError: (error: Error) => {
      const msg = error.message || "";
      if (msg.includes("401")) {
        toast.error("Please sign in to use watchlist");
      } else if (msg.includes("409")) {
        toast.info("Already in your watchlist");
      } else if (msg.includes("404")) {
        toast.error("Stock not found in database");
      } else {
        toast.error("Failed to add to watchlist");
      }
    },
  });
}

export function useRemoveFromWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => removeFromWatchlist(symbol),
    onSuccess: () => {
      haptic("light");
      qc.invalidateQueries({ queryKey: ["watchlist"] });
      toast.success("Removed from watchlist");
    },
    onError: () => {
      toast.error("Failed to remove from watchlist");
    },
  });
}
