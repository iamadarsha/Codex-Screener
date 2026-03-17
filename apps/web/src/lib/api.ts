import { API_BASE_URL } from "./constants";
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
/*  Generic fetch helpers                                              */
/* ------------------------------------------------------------------ */

/** Public API call — no auth required */
async function publicFetch<T>(path: string, init?: RequestInit & { timeoutMs?: number }): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), init?.timeoutMs ?? 15_000);
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

/** Get auth headers from Supabase session (lazy import to avoid SSR issues) */
async function getAuthHeaders(): Promise<Record<string, string>> {
  try {
    if (typeof window === "undefined") return {};
    const { createClient } = await import("./supabase/client");
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) {
      return { Authorization: `Bearer ${data.session.access_token}` };
    }
  } catch {
    // No auth available — continue without token
  }
  return {};
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

export async function fetchFundamentals(
  filters: FundamentalFilters
): Promise<FundamentalData[]> {
  const sp = new URLSearchParams();
  // Map client filter keys → API query param names
  if (filters.pe_min != null) sp.set("pe_min", String(filters.pe_min));
  if (filters.pe_max != null) sp.set("pe_max", String(filters.pe_max));
  if (filters.pb_min != null) sp.set("pb_min", String(filters.pb_min));
  if (filters.pb_max != null) sp.set("pb_max", String(filters.pb_max));
  if (filters.market_cap_min != null) sp.set("market_cap_min", String(filters.market_cap_min));
  if (filters.market_cap_max != null) sp.set("market_cap_max", String(filters.market_cap_max));
  if (filters.roe_min != null) sp.set("roe_min", String(filters.roe_min));
  if (filters.dividend_yield_min != null) sp.set("div_yield_min", String(filters.dividend_yield_min));
  if (filters.debt_to_equity_max != null) sp.set("debt_equity_max", String(filters.debt_to_equity_max));
  const qs = sp.toString();

  // API returns { items: [...], total, page, ... } — extract and remap field names
  const resp = await publicFetch<{ items: Record<string, unknown>[] }>(
    `/api/fundamentals${qs ? `?${qs}` : ""}`
  );
  return (resp.items ?? []).map((r) => ({
    symbol: r.symbol as string,
    name: (r.company_name ?? r.symbol) as string,
    sector: (r.sector ?? "") as string,
    market_cap: r.market_cap != null ? Number(r.market_cap) : 0,
    pe_ratio: r.pe != null ? Number(r.pe) : null,
    pb_ratio: r.pb != null ? Number(r.pb) : null,
    roe: r.roe != null ? Number(r.roe) : null,
    dividend_yield: r.div_yield != null ? Number(r.div_yield) : null,
    debt_to_equity: r.debt_equity != null ? Number(r.debt_equity) : null,
    eps: null,
    book_value: null,
    face_value: null,
  }));
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
