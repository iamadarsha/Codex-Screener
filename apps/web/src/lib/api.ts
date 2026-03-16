import { API_BASE_URL } from "./constants";
import { createClient } from "./supabase/client";
import type {
  AiSuggestionsResponse,
  Alert,
  AlertCreateRequest,
  CustomScanRequest,
  FundamentalData,
  FundamentalFilters,
  IndexData,
  Indicators,
  LivePrice,
  MarketBreadth,
  MarketStatus,
  PrebuiltScan,
  PriceHistory,
  ScanResult,
  SectorData,
  Stock,
  StockListResponse,
  WatchlistItem,
} from "./api-types";

/* ------------------------------------------------------------------ */
/*  Generic fetch helper                                               */
/* ------------------------------------------------------------------ */

async function getAuthHeaders(): Promise<Record<string, string>> {
  try {
    const supabase = createClient();
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error) {
      console.warn("[api] getSession error:", error.message);
    }
    if (session?.access_token) {
      return { Authorization: `Bearer ${session.access_token}` };
    }
    console.warn("[api] No active session — watchlist/alerts will fail");
  } catch (e) {
    console.warn("[api] getAuthHeaders error:", e);
  }
  return {};
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15_000);
  const authHeaders = await getAuthHeaders();
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
        ...(init?.headers ?? {}),
      },
      ...init,
      signal: controller.signal,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`API ${res.status}: ${text || res.statusText}`);
    }
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timeout);
  }
}

/* ------------------------------------------------------------------ */
/*  Stocks                                                             */
/* ------------------------------------------------------------------ */

export function fetchStocks(params?: {
  search?: string;
  page?: number;
  limit?: number;
  nifty50?: boolean;
  nifty500?: boolean;
  sector?: string;
}): Promise<StockListResponse> {
  const sp = new URLSearchParams();
  if (params?.search) sp.set("search", params.search);
  if (params?.page) sp.set("page", String(params.page));
  if (params?.limit) sp.set("limit", String(params.limit));
  if (params?.nifty50) sp.set("nifty50", "true");
  if (params?.nifty500) sp.set("nifty500", "true");
  if (params?.sector) sp.set("sector", params.sector);
  const qs = sp.toString();
  return apiFetch<StockListResponse>(`/api/stocks${qs ? `?${qs}` : ""}`);
}

export function fetchStock(symbol: string): Promise<Stock> {
  return apiFetch<Stock>(`/api/stocks/${symbol}`);
}

/* ------------------------------------------------------------------ */
/*  Screener                                                           */
/* ------------------------------------------------------------------ */

export function fetchPrebuiltScans(): Promise<PrebuiltScan[]> {
  return apiFetch<PrebuiltScan[]>("/api/screener/prebuilt");
}

export function runPrebuiltScan(scanId: string): Promise<ScanResult> {
  return apiFetch<ScanResult>("/api/screener/run", {
    method: "POST",
    body: JSON.stringify({ scan_id: scanId }),
  });
}

export function runCustomScan(req: CustomScanRequest): Promise<ScanResult> {
  return apiFetch<ScanResult>("/api/screener/custom", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/* ------------------------------------------------------------------ */
/*  Prices                                                             */
/* ------------------------------------------------------------------ */

export function fetchLivePrice(symbol: string): Promise<LivePrice> {
  return apiFetch<LivePrice>(`/api/prices/live/${symbol}`);
}

export function fetchLivePrices(symbols: string[]): Promise<LivePrice[]> {
  return apiFetch<LivePrice[]>(
    `/api/prices/live?symbols=${symbols.join(",")}`
  );
}

export function fetchPriceHistory(
  symbol: string,
  timeframe: string
): Promise<PriceHistory> {
  return apiFetch<PriceHistory>(
    `/api/prices/history/${symbol}?timeframe=${timeframe}`
  );
}

export function fetchIndicators(symbol: string): Promise<Indicators> {
  return apiFetch<Indicators>(`/api/prices/indicators/${symbol}`);
}

/* ------------------------------------------------------------------ */
/*  Market                                                             */
/* ------------------------------------------------------------------ */

export function fetchMarketStatus(): Promise<MarketStatus> {
  return apiFetch<MarketStatus>("/api/market/status");
}

export function fetchMarketBreadth(): Promise<MarketBreadth> {
  return apiFetch<MarketBreadth>("/api/market/breadth");
}

export function fetchMarketIndices(): Promise<IndexData[]> {
  return apiFetch<IndexData[]>("/api/market/indices");
}

export function fetchMarketSectors(): Promise<SectorData[]> {
  return apiFetch<SectorData[]>("/api/market/sectors");
}

/* ------------------------------------------------------------------ */
/*  Watchlist                                                          */
/* ------------------------------------------------------------------ */

export function fetchWatchlist(): Promise<WatchlistItem[]> {
  return apiFetch<WatchlistItem[]>("/api/watchlist");
}

export function addToWatchlist(symbol: string): Promise<WatchlistItem> {
  return apiFetch<WatchlistItem>("/api/watchlist", {
    method: "POST",
    body: JSON.stringify({ symbol }),
  });
}

export function removeFromWatchlist(symbol: string): Promise<void> {
  return apiFetch<void>(`/api/watchlist/${symbol}`, {
    method: "DELETE",
  });
}

/* ------------------------------------------------------------------ */
/*  Alerts                                                             */
/* ------------------------------------------------------------------ */

export function fetchAlerts(): Promise<Alert[]> {
  return apiFetch<Alert[]>("/api/alerts");
}

export function createAlert(req: AlertCreateRequest): Promise<Alert> {
  return apiFetch<Alert>("/api/alerts", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/* ------------------------------------------------------------------ */
/*  Fundamentals                                                       */
/* ------------------------------------------------------------------ */

export function fetchFundamentals(
  filters: FundamentalFilters
): Promise<FundamentalData[]> {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) {
    if (v !== undefined && v !== null && v !== "") {
      sp.set(k, String(v));
    }
  }
  const qs = sp.toString();
  return apiFetch<FundamentalData[]>(
    `/api/fundamentals${qs ? `?${qs}` : ""}`
  );
}

/* ------------------------------------------------------------------ */
/*  AI Suggestions                                                     */
/* ------------------------------------------------------------------ */

export function fetchAiSuggestions(): Promise<AiSuggestionsResponse> {
  return apiFetch<AiSuggestionsResponse>("/api/ai-suggestions");
}

export function refreshAiSuggestions(): Promise<AiSuggestionsResponse> {
  return apiFetch<AiSuggestionsResponse>("/api/ai-suggestions/refresh", {
    method: "POST",
  });
}

/* ------------------------------------------------------------------ */
/*  Company Info                                                       */
/* ------------------------------------------------------------------ */

export function fetchCompanyInfo(
  symbol: string
): Promise<import("./api-types").CompanyInfo> {
  return apiFetch<import("./api-types").CompanyInfo>(
    `/api/company/${symbol}`
  );
}
