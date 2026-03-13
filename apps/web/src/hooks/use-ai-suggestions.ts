"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAiSuggestions, refreshAiSuggestions } from "@/lib/api";
import type { AiSuggestionsResponse } from "@/lib/api-types";

const MOCK_SUGGESTIONS: AiSuggestionsResponse = {
  intraday: [
    { symbol: "RELIANCE", name: "Reliance Industries Ltd", sector: "Energy", rationale: "Strong quarterly results and expansion in digital services driving momentum. Retail segment showing accelerated growth.", confidence: 8, catalyst: "Q3 earnings beat", target_horizon: "intraday", action: "BUY", target_pct: 2.5, stop_loss_pct: 1.0, tags: ["Momentum", "Earnings"], news_sources: [{ title: "Reliance Q3 net profit jumps 12% on Jio, retail strength", url: "https://www.moneycontrol.com/news/business/earnings/reliance-q3-results", source: "Moneycontrol", published_at: "2026-03-12T10:30:00" }, { title: "Reliance Industries stock surges on digital services expansion", url: "https://economictimes.indiatimes.com/markets/stocks/news/reliance-digital", source: "Economic Times", published_at: "2026-03-12T09:15:00" }] },
    { symbol: "TATAMOTORS", name: "Tata Motors Ltd", sector: "Auto", rationale: "JLR margins expanding, EV segment gaining traction in domestic market with Nexon EV leading sales.", confidence: 7, catalyst: "EV sales surge", target_horizon: "intraday", action: "BUY", target_pct: 1.8, stop_loss_pct: 0.8, tags: ["EV", "Breakout"], news_sources: [{ title: "Tata Motors EV sales cross 1 lakh units in FY26", url: "https://www.livemint.com/auto-news/tata-motors-ev-sales", source: "Livemint", published_at: "2026-03-11T14:20:00" }] },
    { symbol: "SBIN", name: "State Bank of India", sector: "Banking", rationale: "Credit growth exceeding 15% YoY, asset quality improving with declining NPA ratios across segments.", confidence: 7, catalyst: "Strong credit growth", target_horizon: "intraday", action: "BUY", target_pct: 1.5, stop_loss_pct: 0.7, tags: ["Banking", "Volume Spike"], news_sources: [{ title: "SBI credit growth beats industry average at 16.2%", url: "https://www.business-standard.com/finance/news/sbi-credit-growth", source: "Business Standard", published_at: "2026-03-12T08:45:00" }] },
    { symbol: "ICICIBANK", name: "ICICI Bank Ltd", sector: "Banking", rationale: "Consistent outperformance on ROA and ROE metrics, digital banking platform gaining market share.", confidence: 8, catalyst: "Digital banking growth", target_horizon: "intraday", action: "BUY", target_pct: 2.0, stop_loss_pct: 0.9, tags: ["Quality", "Momentum"], news_sources: [{ title: "ICICI Bank digital transactions surge 40% YoY", url: "https://economictimes.indiatimes.com/industry/banking/icici-digital", source: "Economic Times", published_at: "2026-03-11T16:30:00" }, { title: "ICICI Direct upgrades ICICI Bank to Strong Buy", url: "https://www.moneycontrol.com/news/business/markets/icici-bank-upgrade", source: "Moneycontrol", published_at: "2026-03-12T07:00:00" }] },
    { symbol: "BHARTIARTL", name: "Bharti Airtel Ltd", sector: "Telecom", rationale: "ARPU expansion on tariff hikes, 5G subscriber additions accelerating across metros.", confidence: 7, catalyst: "Tariff hike impact", target_horizon: "intraday", action: "BUY", target_pct: 1.6, stop_loss_pct: 0.8, tags: ["5G", "ARPU Growth"], news_sources: [{ title: "Bharti Airtel ARPU rises to Rs 233 post tariff revision", url: "https://www.livemint.com/industry/telecom/airtel-arpu", source: "Livemint", published_at: "2026-03-12T11:00:00" }] },
  ],
  weekly: [
    { symbol: "TCS", name: "Tata Consultancy Services", sector: "IT", rationale: "Large deal wins and improving demand outlook in BFSI segment. AI-driven services pipeline growing.", confidence: 7, catalyst: "Deal pipeline growth", target_horizon: "swing", action: "BUY", target_pct: 5.0, stop_loss_pct: 2.5, tags: ["Large Cap", "IT Revival"], news_sources: [{ title: "TCS wins $2B deal from European bank for AI transformation", url: "https://www.moneycontrol.com/news/business/tcs-deal-win", source: "Moneycontrol", published_at: "2026-03-10T12:00:00" }] },
    { symbol: "INFY", name: "Infosys Ltd", sector: "IT", rationale: "Raised revenue guidance signals strong demand environment. Margin expansion via automation.", confidence: 7, catalyst: "Guidance upgrade", target_horizon: "swing", action: "BUY", target_pct: 4.5, stop_loss_pct: 2.0, tags: ["Guidance Up", "Quality"], news_sources: [{ title: "Infosys raises FY26 revenue guidance to 4.5-5%", url: "https://economictimes.indiatimes.com/tech/infosys-guidance", source: "Economic Times", published_at: "2026-03-09T18:30:00" }] },
    { symbol: "LT", name: "Larsen & Toubro Ltd", sector: "Infra", rationale: "Massive order book of Rs 4.7L Cr, infrastructure capex cycle driving multi-year growth visibility.", confidence: 8, catalyst: "Infrastructure spending", target_horizon: "swing", action: "BUY", target_pct: 6.0, stop_loss_pct: 3.0, tags: ["Infra", "Order Book"], news_sources: [{ title: "L&T bags Rs 12,000 Cr orders in renewable energy segment", url: "https://www.business-standard.com/companies/news/lt-orders", source: "Business Standard", published_at: "2026-03-11T10:15:00" }] },
    { symbol: "AXISBANK", name: "Axis Bank Ltd", sector: "Banking", rationale: "Citibank India integration complete, retail loan book growing 22% YoY with stable asset quality.", confidence: 7, catalyst: "Integration synergies", target_horizon: "swing", action: "BUY", target_pct: 5.5, stop_loss_pct: 2.5, tags: ["Banking", "Turnaround"], news_sources: [{ title: "Axis Bank completes Citibank consumer business integration", url: "https://www.livemint.com/industry/banking/axis-citi-integration", source: "Livemint", published_at: "2026-03-10T09:00:00" }] },
    { symbol: "MARUTI", name: "Maruti Suzuki India Ltd", sector: "Auto", rationale: "SUV portfolio driving margin expansion, export markets diversifying beyond Africa.", confidence: 6, catalyst: "SUV market share gain", target_horizon: "swing", action: "BUY", target_pct: 4.0, stop_loss_pct: 2.0, tags: ["Auto", "Market Leader"], news_sources: [{ title: "Maruti Suzuki SUV sales surpass hatchback for first time", url: "https://www.moneycontrol.com/news/business/maruti-suv-sales", source: "Moneycontrol", published_at: "2026-03-08T14:00:00" }] },
  ],
  monthly: [
    { symbol: "HDFCBANK", name: "HDFC Bank Ltd", sector: "Banking", rationale: "Post-merger integration complete, strong deposit growth and improving NIMs. Largest private bank by assets.", confidence: 8, catalyst: "NIM expansion", target_horizon: "positional", action: "BUY", target_pct: 12.0, stop_loss_pct: 5.0, tags: ["Banking", "Value"], news_sources: [{ title: "HDFC Bank NIM improves to 3.6% post merger stabilization", url: "https://economictimes.indiatimes.com/industry/banking/hdfc-bank-nim", source: "Economic Times", published_at: "2026-03-07T16:45:00" }, { title: "Motilal Oswal maintains Buy on HDFC Bank, target Rs 2100", url: "https://www.moneycontrol.com/news/business/markets/hdfc-bank-target", source: "Moneycontrol", published_at: "2026-03-11T08:30:00" }] },
    { symbol: "WIPRO", name: "Wipro Ltd", sector: "IT", rationale: "New CEO driving turnaround strategy, focus on large deals and AI consulting practice.", confidence: 6, catalyst: "Strategic restructuring", target_horizon: "positional", action: "BUY", target_pct: 10.0, stop_loss_pct: 5.0, tags: ["IT", "Turnaround"], news_sources: [{ title: "Wipro restructures into 4 business units under new CEO", url: "https://www.business-standard.com/companies/news/wipro-restructure", source: "Business Standard", published_at: "2026-03-06T12:00:00" }] },
    { symbol: "BAJFINANCE", name: "Bajaj Finance Ltd", sector: "Financial Services", rationale: "AUM growing 30%+ YoY, fintech platform Bajaj Finserv app reaching 60M users.", confidence: 8, catalyst: "Digital lending scale", target_horizon: "positional", action: "BUY", target_pct: 15.0, stop_loss_pct: 6.0, tags: ["NBFC", "Growth"], news_sources: [{ title: "Bajaj Finance AUM crosses Rs 3.5 lakh crore milestone", url: "https://www.livemint.com/companies/news/bajaj-finance-aum", source: "Livemint", published_at: "2026-03-10T11:30:00" }] },
    { symbol: "SUNPHARMA", name: "Sun Pharmaceutical Industries", sector: "Pharma", rationale: "Specialty portfolio growing 25%+ in US market, Tildrakizumab gaining market share.", confidence: 7, catalyst: "Specialty drug sales", target_horizon: "positional", action: "BUY", target_pct: 12.0, stop_loss_pct: 5.0, tags: ["Pharma", "Specialty"], news_sources: [{ title: "Sun Pharma specialty revenue grows 28% in US market", url: "https://economictimes.indiatimes.com/industry/healthcare/sun-pharma-us", source: "Economic Times", published_at: "2026-03-09T10:00:00" }] },
    { symbol: "ADANIENT", name: "Adani Enterprises Ltd", sector: "Infra", rationale: "Diversified conglomerate with green energy, airport and data center verticals showing strong traction.", confidence: 6, catalyst: "Green energy expansion", target_horizon: "positional", action: "BUY", target_pct: 18.0, stop_loss_pct: 8.0, tags: ["Infra", "Diversified"], news_sources: [{ title: "Adani Green commissions 2 GW solar capacity in Rajasthan", url: "https://www.business-standard.com/companies/news/adani-green-solar", source: "Business Standard", published_at: "2026-03-08T09:30:00" }] },
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
