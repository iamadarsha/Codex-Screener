import type { PrebuiltScan } from "./api-types";

// Scan definitions — these are UI configuration, not demo data
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
