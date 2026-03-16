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
  } catch (e) {
    console.warn("[api] getAuthHeaders error:", e);
  }
  return {};
}

/** Public API call — no auth header, faster */
async function publicFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
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

/** Authenticated API call — includes Bearer token */
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);
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
  return publicFetch<StockListResponse>(`/api/stocks${qs ? `?${qs}` : ""}`);
}

export function fetchStock(symbol: string): Promise<Stock> {
  return publicFetch<Stock>(`/api/stocks/${symbol}`);
}

/* ------------------------------------------------------------------ */
/*  Screener                                                           */
/* ------------------------------------------------------------------ */

export function fetchPrebuiltScans(): Promise<PrebuiltScan[]> {
  return publicFetch<PrebuiltScan[]>("/api/screener/prebuilt");
}

export function runPrebuiltScan(scanId: string): Promise<ScanResult> {
  return publicFetch<ScanResult>("/api/screener/run", {
    method: "POST",
    body: JSON.stringify({ scan_id: scanId }),
  });
}

export function runCustomScan(req: CustomScanRequest): Promise<ScanResult> {
  return publicFetch<ScanResult>("/api/screener/custom", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/* ------------------------------------------------------------------ */
/*  Prices                                                             */
/* ------------------------------------------------------------------ */

export function fetchLivePrice(symbol: string): Promise<LivePrice> {
  return publicFetch<LivePrice>(`/api/prices/live/${symbol}`);
}

export function fetchLivePrices(symbols: string[]): Promise<LivePrice[]> {
  return publicFetch<LivePrice[]>(
    `/api/prices/live?symbols=${symbols.join(",")}`
  );
}

export function fetchPriceHistory(
  symbol: string,
  timeframe: string
): Promise<PriceHistory> {
  return publicFetch<PriceHistory>(
    `/api/prices/history/${symbol}?timeframe=${timeframe}`
  );
}

export function fetchIndicators(symbol: string): Promise<Indicators> {
  return publicFetch<Indicators>(`/api/prices/indicators/${symbol}`);
}

/* ------------------------------------------------------------------ */
/*  Market                                                             */
/* ------------------------------------------------------------------ */

export function fetchMarketStatus(): Promise<MarketStatus> {
  return publicFetch<MarketStatus>("/api/market/status");
}

export function fetchMarketBreadth(): Promise<MarketBreadth> {
  return publicFetch<MarketBreadth>("/api/market/breadth");
}

export function fetchMarketIndices(): Promise<IndexData[]> {
  return publicFetch<IndexData[]>("/api/market/indices");
}

export function fetchMarketSectors(): Promise<SectorData[]> {
  return publicFetch<SectorData[]>("/api/market/sectors");
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
  return publicFetch<FundamentalData[]>(
    `/api/fundamentals${qs ? `?${qs}` : ""}`
  );
}

/* ------------------------------------------------------------------ */
/*  AI Suggestions                                                     */
/* ------------------------------------------------------------------ */

export function fetchAiSuggestions(): Promise<AiSuggestionsResponse> {
  return publicFetch<AiSuggestionsResponse>("/api/ai-suggestions");
}

export function refreshAiSuggestions(): Promise<AiSuggestionsResponse> {
  return publicFetch<AiSuggestionsResponse>("/api/ai-suggestions/refresh", {
    method: "POST",
  });
}

/* ------------------------------------------------------------------ */
/*  Company Info                                                       */
/* ------------------------------------------------------------------ */

export function fetchCompanyInfo(
  symbol: string
): Promise<import("./api-types").CompanyInfo> {
  return publicFetch<import("./api-types").CompanyInfo>(
    `/api/company/${symbol}`
  );
}
