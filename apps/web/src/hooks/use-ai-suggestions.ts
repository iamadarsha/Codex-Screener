"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAiSuggestions, refreshAiSuggestions } from "@/lib/api";
import type { AiSuggestionsResponse } from "@/lib/api-types";

const MOCK_SUGGESTIONS: AiSuggestionsResponse = {
  suggestions: [
    {
      symbol: "RELIANCE",
      name: "Reliance Industries Ltd",
      sector: "Energy",
      rationale:
        "Strong quarterly results and expansion in digital services driving momentum.",
      confidence: 8,
      catalyst: "Q3 earnings beat",
      target_horizon: "swing",
    },
    {
      symbol: "TCS",
      name: "Tata Consultancy Services",
      sector: "IT",
      rationale:
        "Large deal wins and improving demand outlook in BFSI segment.",
      confidence: 7,
      catalyst: "Deal pipeline growth",
      target_horizon: "positional",
    },
    {
      symbol: "HDFCBANK",
      name: "HDFC Bank Ltd",
      sector: "Banking",
      rationale:
        "Post-merger integration complete, strong deposit growth and improving NIMs.",
      confidence: 8,
      catalyst: "NIM expansion",
      target_horizon: "positional",
    },
    {
      symbol: "INFY",
      name: "Infosys Ltd",
      sector: "IT",
      rationale:
        "Raised revenue guidance signals strong demand environment.",
      confidence: 7,
      catalyst: "Guidance upgrade",
      target_horizon: "swing",
    },
    {
      symbol: "BHARTIARTL",
      name: "Bharti Airtel Ltd",
      sector: "Telecom",
      rationale:
        "5G subscriber growth accelerating, ARPU expansion on tariff hikes.",
      confidence: 7,
      catalyst: "Tariff hike impact",
      target_horizon: "positional",
    },
  ],
  generated_at: new Date().toISOString(),
  headline_count: 15,
};

export function useAiSuggestions() {
  const query = useQuery({
    queryKey: ["aiSuggestions"],
    queryFn: fetchAiSuggestions,
    staleTime: 60_000 * 10,
    retry: 1,
  });

  return {
    ...query,
    data: query.data ?? (query.isError ? MOCK_SUGGESTIONS : undefined),
  };
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
