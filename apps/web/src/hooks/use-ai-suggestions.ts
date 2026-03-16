"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAiSuggestions, refreshAiSuggestions } from "@/lib/api";
import type { AiSuggestionsResponse } from "@/lib/api-types";

export function useAiSuggestions() {
  return useQuery({
    queryKey: ["aiSuggestions"],
    queryFn: fetchAiSuggestions,
    staleTime: 60_000 * 10,
    retry: 1,
  });
}

export function useRefreshAiSuggestions() {
  const qc = useQueryClient();
  return useMutation<AiSuggestionsResponse, Error>({
    mutationFn: refreshAiSuggestions,
    onSuccess: (data) => {
      qc.setQueryData(["aiSuggestions"], data);
    },
  });
}
