/**
 * Local NSE stock search utility.
 * Provides fast client-side filtering for the stock search bar.
 */

export interface NseStock {
  symbol: string;
  name: string;
  sector?: string;
}

// Populated at runtime from the API; empty until first load.
let _stockCache: NseStock[] = [];

export function setStockCache(stocks: NseStock[]) {
  _stockCache = stocks;
}

export function searchLocalStocks(query: string, limit = 10): NseStock[] {
  if (!query || query.length < 1) return [];
  const q = query.toUpperCase();
  return _stockCache
    .filter(
      (s) =>
        s.symbol.toUpperCase().includes(q) ||
        s.name.toUpperCase().includes(q)
    )
    .slice(0, limit);
}
