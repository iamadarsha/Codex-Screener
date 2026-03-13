"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAiSuggestions, refreshAiSuggestions } from "@/lib/api";
import type { AiSuggestionsResponse } from "@/lib/api-types";

const MOCK_SUGGESTIONS: AiSuggestionsResponse = {
  intraday: [
    { symbol: "RELIANCE", name: "Reliance Industries Ltd", sector: "Energy", rationale: "Strong quarterly results and expansion in digital services driving momentum. Retail segment showing accelerated growth.", confidence: 8, catalyst: "Q3 earnings beat", target_horizon: "intraday", action: "BUY", target_pct: 2.5, stop_loss_pct: 1.0, tags: ["Momentum", "Earnings"] },
    { symbol: "TATAMOTORS", name: "Tata Motors Ltd", sector: "Auto", rationale: "JLR margins expanding, EV segment gaining traction in domestic market with Nexon EV leading sales.", confidence: 7, catalyst: "EV sales surge", target_horizon: "intraday", action: "BUY", target_pct: 1.8, stop_loss_pct: 0.8, tags: ["EV", "Breakout"] },
    { symbol: "SBIN", name: "State Bank of India", sector: "Banking", rationale: "Credit growth exceeding 15% YoY, asset quality improving with declining NPA ratios across segments.", confidence: 7, catalyst: "Strong credit growth", target_horizon: "intraday", action: "BUY", target_pct: 1.5, stop_loss_pct: 0.7, tags: ["Banking", "Volume Spike"] },
    { symbol: "ICICIBANK", name: "ICICI Bank Ltd", sector: "Banking", rationale: "Consistent outperformance on ROA and ROE metrics, digital banking platform gaining market share.", confidence: 8, catalyst: "Digital banking growth", target_horizon: "intraday", action: "BUY", target_pct: 2.0, stop_loss_pct: 0.9, tags: ["Quality", "Momentum"] },
    { symbol: "BHARTIARTL", name: "Bharti Airtel Ltd", sector: "Telecom", rationale: "ARPU expansion on tariff hikes, 5G subscriber additions accelerating across metros.", confidence: 7, catalyst: "Tariff hike impact", target_horizon: "intraday", action: "BUY", target_pct: 1.6, stop_loss_pct: 0.8, tags: ["5G", "ARPU Growth"] },
  ],
  weekly: [
    { symbol: "TCS", name: "Tata Consultancy Services", sector: "IT", rationale: "Large deal wins and improving demand outlook in BFSI segment. AI-driven services pipeline growing.", confidence: 7, catalyst: "Deal pipeline growth", target_horizon: "swing", action: "BUY", target_pct: 5.0, stop_loss_pct: 2.5, tags: ["Large Cap", "IT Revival"] },
    { symbol: "INFY", name: "Infosys Ltd", sector: "IT", rationale: "Raised revenue guidance signals strong demand environment. Margin expansion via automation.", confidence: 7, catalyst: "Guidance upgrade", target_horizon: "swing", action: "BUY", target_pct: 4.5, stop_loss_pct: 2.0, tags: ["Guidance Up", "Quality"] },
    { symbol: "LT", name: "Larsen & Toubro Ltd", sector: "Infra", rationale: "Massive order book of Rs 4.7L Cr, infrastructure capex cycle driving multi-year growth visibility.", confidence: 8, catalyst: "Infrastructure spending", target_horizon: "swing", action: "BUY", target_pct: 6.0, stop_loss_pct: 3.0, tags: ["Infra", "Order Book"] },
    { symbol: "AXISBANK", name: "Axis Bank Ltd", sector: "Banking", rationale: "Citibank India integration complete, retail loan book growing 22% YoY with stable asset quality.", confidence: 7, catalyst: "Integration synergies", target_horizon: "swing", action: "BUY", target_pct: 5.5, stop_loss_pct: 2.5, tags: ["Banking", "Turnaround"] },
    { symbol: "MARUTI", name: "Maruti Suzuki India Ltd", sector: "Auto", rationale: "SUV portfolio driving margin expansion, export markets diversifying beyond Africa.", confidence: 6, catalyst: "SUV market share gain", target_horizon: "swing", action: "BUY", target_pct: 4.0, stop_loss_pct: 2.0, tags: ["Auto", "Market Leader"] },
  ],
  monthly: [
    { symbol: "HDFCBANK", name: "HDFC Bank Ltd", sector: "Banking", rationale: "Post-merger integration complete, strong deposit growth and improving NIMs. Largest private bank by assets.", confidence: 8, catalyst: "NIM expansion", target_horizon: "positional", action: "BUY", target_pct: 12.0, stop_loss_pct: 5.0, tags: ["Banking", "Value"] },
    { symbol: "WIPRO", name: "Wipro Ltd", sector: "IT", rationale: "New CEO driving turnaround strategy, focus on large deals and AI consulting practice.", confidence: 6, catalyst: "Strategic restructuring", target_horizon: "positional", action: "BUY", target_pct: 10.0, stop_loss_pct: 5.0, tags: ["IT", "Turnaround"] },
    { symbol: "BAJFINANCE", name: "Bajaj Finance Ltd", sector: "Financial Services", rationale: "AUM growing 30%+ YoY, fintech platform Bajaj Finserv app reaching 60M users.", confidence: 8, catalyst: "Digital lending scale", target_horizon: "positional", action: "BUY", target_pct: 15.0, stop_loss_pct: 6.0, tags: ["NBFC", "Growth"] },
    { symbol: "SUNPHARMA", name: "Sun Pharmaceutical Industries", sector: "Pharma", rationale: "Specialty portfolio growing 25%+ in US market, Tildrakizumab gaining market share.", confidence: 7, catalyst: "Specialty drug sales", target_horizon: "positional", action: "BUY", target_pct: 12.0, stop_loss_pct: 5.0, tags: ["Pharma", "Specialty"] },
    { symbol: "ADANIENT", name: "Adani Enterprises Ltd", sector: "Infra", rationale: "Diversified conglomerate with green energy, airport and data center verticals showing strong traction.", confidence: 6, catalyst: "Green energy expansion", target_horizon: "positional", action: "BUY", target_pct: 18.0, stop_loss_pct: 8.0, tags: ["Infra", "Diversified"] },
  ],
  generated_at: new Date().toISOString(),
  headline_count: 25,
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
