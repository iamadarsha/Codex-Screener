import type { IndexData, MarketBreadth, MarketStatus, PrebuiltScan, ScanResultItem, LivePrice } from "./api-types";

export const MOCK_INDICES: IndexData[] = [
  { symbol: "NIFTY50", name: "NIFTY 50", last: 24850.25, change: 125.50, change_pct: 0.51 },
  { symbol: "NIFTYBANK", name: "NIFTY BANK", last: 52150.80, change: -85.30, change_pct: -0.16 },
  { symbol: "NIFTYIT", name: "NIFTY IT", last: 34200.15, change: 210.45, change_pct: 0.62 },
  { symbol: "NIFTYPHARMA", name: "NIFTY PHARMA", last: 19850.60, change: 45.20, change_pct: 0.23 },
  { symbol: "NIFTYAUTO", name: "NIFTY AUTO", last: 25100.35, change: -120.80, change_pct: -0.48 },
  { symbol: "INDIAVIX", name: "INDIA VIX", last: 13.25, change: -0.45, change_pct: -3.29 },
];

export const MOCK_MARKET_STATUS: MarketStatus = {
  is_open: false,
  status: "closed",
};

export const MOCK_BREADTH: MarketBreadth = {
  advances: 28,
  declines: 20,
  unchanged: 2,
  total: 50,
  advance_decline_ratio: 1.4,
};

export const MOCK_PREBUILT_SCANS: PrebuiltScan[] = [
  { id: "rsi_oversold", name: "RSI Oversold", description: "RSI(14) below 30 - reversal candidates", category: "Momentum", icon: "activity" },
  { id: "rsi_overbought", name: "RSI Overbought", description: "RSI(14) above 70 - overextended", category: "Momentum", icon: "activity" },
  { id: "bullish_ema_crossover", name: "Bullish EMA Cross", description: "EMA(9) crosses above EMA(21)", category: "Momentum", icon: "trending-up" },
  { id: "bearish_ema_crossover", name: "Bearish EMA Cross", description: "EMA(9) crosses below EMA(21)", category: "Momentum", icon: "trending-down" },
  { id: "price_above_sma200", name: "Above SMA(200)", description: "Long-term uptrend confirmation", category: "Moving Averages", icon: "arrow-up" },
  { id: "price_below_sma200", name: "Below SMA(200)", description: "Long-term downtrend", category: "Moving Averages", icon: "arrow-down" },
  { id: "volume_spike", name: "Volume Spike (2x)", description: "Volume > 2x 20-period average", category: "Volume", icon: "bar-chart-2" },
  { id: "bollinger_squeeze", name: "Bollinger Squeeze", description: "Bandwidth < 4% - volatility contraction", category: "Pattern", icon: "minimize-2" },
  { id: "macd_bullish_cross", name: "MACD Bullish Cross", description: "MACD crosses above signal line", category: "Momentum", icon: "zap" },
  { id: "near_52_week_high", name: "Near 52W High", description: "Within 5% of 52-week high", category: "Breakout", icon: "trophy" },
  { id: "orb_breakout_long", name: "ORB Breakout Long", description: "Above opening range high", category: "Intraday", icon: "sunrise" },
  { id: "bullish_engulfing", name: "Bullish Engulfing", description: "Bullish engulfing pattern", category: "Pattern", icon: "shield" },
];

export const MOCK_STOCKS: LivePrice[] = [
  { symbol: "RELIANCE", ltp: 2945.50, open: 2930, high: 2960, low: 2920, close: 2945.50, prev_close: 2918.75, change: 26.75, change_pct: 0.92, volume: 8524610, timestamp: new Date().toISOString() },
  { symbol: "TCS", ltp: 3852.25, open: 3840, high: 3870, low: 3835, close: 3852.25, prev_close: 3828.50, change: 23.75, change_pct: 0.62, volume: 3215840, timestamp: new Date().toISOString() },
  { symbol: "INFY", ltp: 1628.30, open: 1620, high: 1640, low: 1615, close: 1628.30, prev_close: 1612.80, change: 15.50, change_pct: 0.96, volume: 6842150, timestamp: new Date().toISOString() },
  { symbol: "HDFCBANK", ltp: 1725.80, open: 1730, high: 1740, low: 1718, close: 1725.80, prev_close: 1735.20, change: -9.40, change_pct: -0.54, volume: 5124300, timestamp: new Date().toISOString() },
  { symbol: "ICICIBANK", ltp: 1285.60, open: 1280, high: 1295, low: 1275, close: 1285.60, prev_close: 1270.50, change: 15.10, change_pct: 1.19, volume: 4521680, timestamp: new Date().toISOString() },
  { symbol: "TATAMOTORS", ltp: 745.90, open: 740, high: 752, low: 738, close: 745.90, prev_close: 738.20, change: 7.70, change_pct: 1.04, volume: 12548900, timestamp: new Date().toISOString() },
  { symbol: "SBIN", ltp: 812.45, open: 808, high: 818, low: 805, close: 812.45, prev_close: 806.30, change: 6.15, change_pct: 0.76, volume: 9875420, timestamp: new Date().toISOString() },
  { symbol: "WIPRO", ltp: 462.75, open: 458, high: 465, low: 456, close: 462.75, prev_close: 455.80, change: 6.95, change_pct: 1.52, volume: 5648210, timestamp: new Date().toISOString() },
];

// Simulate live data updates
export function getRandomPriceUpdate(stocks: LivePrice[]): LivePrice[] {
  return stocks.map(stock => {
    if (Math.random() > 0.7) return stock; // 30% chance of update
    const changePct = (Math.random() - 0.48) * 0.5; // slight bullish bias
    const newLtp = +(stock.ltp * (1 + changePct / 100)).toFixed(2);
    const change = +(newLtp - stock.prev_close).toFixed(2);
    const pct = +((change / stock.prev_close) * 100).toFixed(2);
    return { ...stock, ltp: newLtp, close: newLtp, change, change_pct: pct, high: Math.max(stock.high, newLtp), low: Math.min(stock.low, newLtp), timestamp: new Date().toISOString() };
  });
}
