import type { PrebuiltScan, IndexData, MarketStatus, MarketBreadth } from "./api-types";

export const MOCK_INDICES: IndexData[] = [
  { symbol: "NIFTY50", name: "NIFTY 50", value: 23340.65, last: 23340.65, change: -95.30, change_pct: -0.41 },
  { symbol: "NIFTYBANK", name: "NIFTY BANK", value: 49520.10, last: 49520.10, change: 185.40, change_pct: 0.38 },
  { symbol: "NIFTYIT", name: "NIFTY IT", value: 36120.75, last: 36120.75, change: -210.55, change_pct: -0.58 },
  { symbol: "NIFTYPHARMA", name: "NIFTY PHARMA", value: 19780.30, last: 19780.30, change: 42.10, change_pct: 0.21 },
  { symbol: "NIFTYAUTO", name: "NIFTY AUTO", value: 22050.45, last: 22050.45, change: -88.60, change_pct: -0.40 },
  { symbol: "INDIAVIX", name: "INDIA VIX", value: 14.35, last: 14.35, change: 0.62, change_pct: 4.52 },
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

export const PREBUILT_SCAN_DEFINITIONS: PrebuiltScan[] = [
  { id: "rsi_oversold", name: "RSI Oversold", description: "RSI(14) below 30 - reversal candidates", category: "Momentum", icon: "activity" },
  { id: "rsi_overbought", name: "RSI Overbought", description: "RSI(14) above 70 - overextended", category: "Momentum", icon: "activity" },
  { id: "bullish_ema_crossover", name: "Bullish EMA Cross", description: "EMA(9) crosses above EMA(21)", category: "Momentum", icon: "trending-up" },
  { id: "bearish_ema_crossover", name: "Bearish EMA Cross", description: "EMA(9) crosses below EMA(21)", category: "Momentum", icon: "trending-down" },
  { id: "price_above_sma200", name: "Above SMA(200)", description: "Long-term uptrend confirmation", category: "Moving Averages", icon: "arrow-up" },
  { id: "price_below_sma200", name: "Below SMA(200)", description: "Long-term downtrend", category: "Moving Averages", icon: "arrow-down" },
  { id: "volume_spike", name: "Volume Spike (2x)", description: "Volume > 2× 20-period average", category: "Volume", icon: "bar-chart-2" },
  { id: "bollinger_squeeze", name: "Bollinger Squeeze", description: "Bandwidth < 4% - volatility contraction", category: "Pattern", icon: "minimize-2" },
  { id: "macd_bullish_cross", name: "MACD Bullish Cross", description: "MACD crosses above signal line", category: "Momentum", icon: "zap" },
  { id: "macd_bearish_cross", name: "MACD Bearish Cross", description: "MACD crosses below signal line", category: "Momentum", icon: "zap-off" },
  { id: "near_52_week_high", name: "Near 52W High", description: "Within 5% of 52-week high", category: "Breakout", icon: "trophy" },
  { id: "orb_breakout_long", name: "ORB Breakout Long", description: "Above opening range high", category: "Intraday", icon: "sunrise" },
  { id: "bullish_engulfing", name: "Bullish Engulfing", description: "Bullish engulfing pattern", category: "Pattern", icon: "shield" },
];
