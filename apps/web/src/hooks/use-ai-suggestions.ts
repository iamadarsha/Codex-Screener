"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAiSuggestions, refreshAiSuggestions } from "@/lib/api";
import type { AiSuggestionsResponse } from "@/lib/api-types";

const MOCK_SUGGESTIONS: AiSuggestionsResponse = {
  intraday: [
    {
      symbol: "RELIANCE",
      name: "Reliance Industries Ltd",
      sector: "Energy",
      rationale:
        "Strong quarterly results and expansion in digital services driving momentum.",
      confidence: 8,
      catalyst: "Q3 earnings beat",
      target_horizon: "intraday",
      action: "BUY",
      target_pct: 2.5,
      stop_loss_pct: 1.0,
      tags: ["Momentum", "Earnings"],
    },
    {
      symbol: "TATAMOTORS",
      name: "Tata Motors Ltd",
      sector: "Auto",
      rationale:
        "JLR margins expanding, EV segment gaining traction in domestic market.",
      confidence: 7,
      catalyst: "EV sales surge",
      target_horizon: "intraday",
      action: "BUY",
      target_pct: 1.8,
      stop_loss_pct: 0.8,
      tags: ["EV", "Breakout"],
    },
  ],
  weekly: [
    {
      symbol: "TCS",
      name: "Tata Consultancy Services",
      sector: "IT",
      rationale:
        "Large deal wins and improving demand outlook in BFSI segment.",
      confidence: 7,
      catalyst: "Deal pipeline growth",
      target_horizon: "swing",
      action: "BUY",
      target_pct: 5.0,
      stop_loss_pct: 2.5,
      tags: ["Large Cap", "IT Revival"],
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
      action: "BUY",
      target_pct: 4.5,
      stop_loss_pct: 2.0,
      tags: ["Guidance Up", "Quality"],
    },
  ],
  monthly: [
    {
      symbol: "HDFCBANK",
      name: "HDFC Bank Ltd",
      sector: "Banking",
      rationale:
        "Post-merger integration complete, strong deposit growth and improving NIMs.",
      confidence: 8,
      catalyst: "NIM expansion",
      target_horizon: "positional",
      action: "BUY",
      target_pct: 12.0,
      stop_loss_pct: 5.0,
      tags: ["Banking", "Value"],
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
      action: "BUY",
      target_pct: 15.0,
      stop_loss_pct: 6.0,
      tags: ["5G", "ARPU Growth"],
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

  const hasEmptyData =
    query.data &&
    !query.data.intraday?.length &&
    !query.data.weekly?.length &&
    !query.data.monthly?.length;

  return {
    ...query,
    data:
      query.data && !hasEmptyData
        ? query.data
        : query.isError || hasEmptyData
          ? MOCK_SUGGESTIONS
          : undefined,
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
