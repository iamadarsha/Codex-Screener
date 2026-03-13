import type { IndexData, MarketBreadth, MarketStatus, PrebuiltScan, ScanResultItem, LivePrice, FundamentalData } from "./api-types";

export const MOCK_INDICES: IndexData[] = [
  { symbol: "NIFTY50", name: "NIFTY 50", last: 23340.65, change: -95.30, change_pct: -0.41 },
  { symbol: "NIFTYBANK", name: "NIFTY BANK", last: 49520.10, change: 185.40, change_pct: 0.38 },
  { symbol: "NIFTYIT", name: "NIFTY IT", last: 36120.75, change: -210.55, change_pct: -0.58 },
  { symbol: "NIFTYPHARMA", name: "NIFTY PHARMA", last: 19780.30, change: 42.10, change_pct: 0.21 },
  { symbol: "NIFTYAUTO", name: "NIFTY AUTO", last: 22050.45, change: -88.60, change_pct: -0.40 },
  { symbol: "INDIAVIX", name: "INDIA VIX", last: 14.35, change: 0.62, change_pct: 4.52 },
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

export const MOCK_SCAN_RESULTS: ScanResultItem[] = [
  { symbol: "RELIANCE", company_name: "Reliance Industries", sector: "Energy", ltp: 2945.50, change_pct: 0.92, volume: 8524610, rsi_14: 28.5, ema_status: "Bullish", matched_conditions: ["RSI Oversold", "Volume Spike"] },
  { symbol: "TATAMOTORS", company_name: "Tata Motors", sector: "Automobile", ltp: 745.90, change_pct: 1.04, volume: 12548900, rsi_14: 42.3, ema_status: "Bullish", matched_conditions: ["Bullish EMA Cross"] },
  { symbol: "SBIN", company_name: "State Bank of India", sector: "Banking", ltp: 812.45, change_pct: 0.76, volume: 9875420, rsi_14: 55.1, ema_status: "Bullish", matched_conditions: ["Volume Spike", "Above SMA(200)"] },
  { symbol: "ICICIBANK", company_name: "ICICI Bank", sector: "Banking", ltp: 1285.60, change_pct: 1.19, volume: 4521680, rsi_14: 62.7, ema_status: "Bullish", matched_conditions: ["Near 52W High"] },
  { symbol: "BHARTIARTL", company_name: "Bharti Airtel", sector: "Telecom", ltp: 1542.30, change_pct: 0.65, volume: 3284500, rsi_14: 58.9, ema_status: "Bullish", matched_conditions: ["MACD Bullish Cross"] },
  { symbol: "LT", company_name: "Larsen & Toubro", sector: "Infrastructure", ltp: 3425.80, change_pct: -0.32, volume: 2154800, rsi_14: 48.2, ema_status: "Bearish", matched_conditions: ["Bollinger Squeeze"] },
  { symbol: "HDFCBANK", company_name: "HDFC Bank", sector: "Banking", ltp: 1725.80, change_pct: -0.54, volume: 5124300, rsi_14: 45.6, ema_status: "Bearish", matched_conditions: ["Price Above SMA(200)"] },
  { symbol: "INFY", company_name: "Infosys", sector: "IT", ltp: 1628.30, change_pct: 0.96, volume: 6842150, rsi_14: 52.4, ema_status: "Bullish", matched_conditions: ["Bullish Engulfing"] },
  { symbol: "TCS", company_name: "Tata Consultancy", sector: "IT", ltp: 3852.25, change_pct: 0.62, volume: 3215840, rsi_14: 56.8, ema_status: "Bullish", matched_conditions: ["Above SMA(200)"] },
  { symbol: "WIPRO", company_name: "Wipro", sector: "IT", ltp: 462.75, change_pct: 1.52, volume: 5648210, rsi_14: 34.2, ema_status: "Bearish", matched_conditions: ["RSI Oversold"] },
];

export const MOCK_FUNDAMENTALS: FundamentalData[] = [
  { symbol: "RELIANCE", name: "Reliance Industries", sector: "Energy", market_cap: 1920000, pe_ratio: 28.5, pb_ratio: 2.8, dividend_yield: 0.35, roe: 12.4, debt_to_equity: 0.42, eps: 103.30, book_value: 1052.00, face_value: 10 },
  { symbol: "TCS", name: "Tata Consultancy", sector: "IT", market_cap: 1410000, pe_ratio: 32.1, pb_ratio: 14.2, dividend_yield: 1.18, roe: 48.5, debt_to_equity: 0.05, eps: 120.00, book_value: 271.00, face_value: 1 },
  { symbol: "HDFCBANK", name: "HDFC Bank", sector: "Banking", market_cap: 1310000, pe_ratio: 19.8, pb_ratio: 3.1, dividend_yield: 1.12, roe: 16.8, debt_to_equity: null, eps: 87.15, book_value: 556.80, face_value: 1 },
  { symbol: "INFY", name: "Infosys", sector: "IT", market_cap: 680000, pe_ratio: 27.4, pb_ratio: 8.9, dividend_yield: 2.15, roe: 33.2, debt_to_equity: 0.08, eps: 59.40, book_value: 183.00, face_value: 5 },
  { symbol: "ICICIBANK", name: "ICICI Bank", sector: "Banking", market_cap: 905000, pe_ratio: 18.2, pb_ratio: 3.4, dividend_yield: 0.78, roe: 18.5, debt_to_equity: null, eps: 70.60, book_value: 378.20, face_value: 2 },
  { symbol: "BHARTIARTL", name: "Bharti Airtel", sector: "Telecom", market_cap: 870000, pe_ratio: 72.5, pb_ratio: 8.1, dividend_yield: 0.52, roe: 11.8, debt_to_equity: 1.85, eps: 21.30, book_value: 190.40, face_value: 5 },
  { symbol: "SBIN", name: "State Bank of India", sector: "Banking", market_cap: 725000, pe_ratio: 10.5, pb_ratio: 1.9, dividend_yield: 1.72, roe: 19.2, debt_to_equity: null, eps: 77.40, book_value: 427.60, face_value: 1 },
  { symbol: "LT", name: "Larsen & Toubro", sector: "Infrastructure", market_cap: 470000, pe_ratio: 34.8, pb_ratio: 5.6, dividend_yield: 0.88, roe: 16.1, debt_to_equity: 1.12, eps: 98.40, book_value: 611.80, face_value: 2 },
  { symbol: "TATAMOTORS", name: "Tata Motors", sector: "Automobile", market_cap: 280000, pe_ratio: 8.2, pb_ratio: 3.5, dividend_yield: 0.40, roe: 42.8, debt_to_equity: 0.95, eps: 90.90, book_value: 213.10, face_value: 2 },
  { symbol: "WIPRO", name: "Wipro", sector: "IT", market_cap: 242000, pe_ratio: 23.6, pb_ratio: 3.8, dividend_yield: 0.22, roe: 16.3, debt_to_equity: 0.18, eps: 19.60, book_value: 121.80, face_value: 2 },
  { symbol: "BAJFINANCE", name: "Bajaj Finance", sector: "NBFC", market_cap: 425000, pe_ratio: 30.2, pb_ratio: 6.8, dividend_yield: 0.44, roe: 22.5, debt_to_equity: 3.2, eps: 228.50, book_value: 1015.00, face_value: 2 },
  { symbol: "SUNPHARMA", name: "Sun Pharma", sector: "Pharma", market_cap: 380000, pe_ratio: 38.5, pb_ratio: 7.2, dividend_yield: 0.65, roe: 18.7, debt_to_equity: 0.12, eps: 41.20, book_value: 220.60, face_value: 1 },
  { symbol: "MARUTI", name: "Maruti Suzuki", sector: "Automobile", market_cap: 365000, pe_ratio: 26.8, pb_ratio: 5.9, dividend_yield: 0.72, roe: 22.1, debt_to_equity: 0.02, eps: 450.80, book_value: 2045.00, face_value: 5 },
  { symbol: "AXISBANK", name: "Axis Bank", sector: "Banking", market_cap: 340000, pe_ratio: 14.5, pb_ratio: 2.3, dividend_yield: 0.09, roe: 16.4, debt_to_equity: null, eps: 76.20, book_value: 480.30, face_value: 2 },
  { symbol: "ADANIENT", name: "Adani Enterprises", sector: "Conglomerate", market_cap: 310000, pe_ratio: 85.2, pb_ratio: 12.4, dividend_yield: 0.05, roe: 14.6, debt_to_equity: 1.45, eps: 28.80, book_value: 197.50, face_value: 1 },
];

export const MOCK_SCAN_RESULTS_BY_ID: Record<string, ScanResultItem[]> = {
  rsi_oversold: [
    { symbol: "WIPRO", company_name: "Wipro", sector: "IT", ltp: 462.75, change_pct: -1.82, volume: 5648210, rsi_14: 22.4, ema_status: "Bearish", matched_conditions: ["RSI(14) < 30"] },
    { symbol: "TATASTEEL", company_name: "Tata Steel", sector: "Metals", ltp: 128.40, change_pct: -2.15, volume: 18542300, rsi_14: 25.1, ema_status: "Bearish", matched_conditions: ["RSI(14) < 30"] },
    { symbol: "HINDALCO", company_name: "Hindalco Industries", sector: "Metals", ltp: 485.60, change_pct: -1.45, volume: 7824500, rsi_14: 26.8, ema_status: "Bearish", matched_conditions: ["RSI(14) < 30"] },
    { symbol: "INDUSINDBK", company_name: "IndusInd Bank", sector: "Banking", ltp: 1425.30, change_pct: -2.85, volume: 4215600, rsi_14: 23.5, ema_status: "Bearish", matched_conditions: ["RSI(14) < 30"] },
    { symbol: "COALINDIA", company_name: "Coal India", sector: "Mining", ltp: 385.20, change_pct: -1.12, volume: 6542100, rsi_14: 28.9, ema_status: "Bearish", matched_conditions: ["RSI(14) < 30"] },
  ],
  rsi_overbought: [
    { symbol: "BHARTIARTL", company_name: "Bharti Airtel", sector: "Telecom", ltp: 1542.30, change_pct: 2.15, volume: 3284500, rsi_14: 78.2, ema_status: "Bullish", matched_conditions: ["RSI(14) > 70"] },
    { symbol: "ICICIBANK", company_name: "ICICI Bank", sector: "Banking", ltp: 1285.60, change_pct: 1.82, volume: 4521680, rsi_14: 74.5, ema_status: "Bullish", matched_conditions: ["RSI(14) > 70"] },
    { symbol: "BAJFINANCE", company_name: "Bajaj Finance", sector: "NBFC", ltp: 6890.50, change_pct: 1.95, volume: 2145800, rsi_14: 76.1, ema_status: "Bullish", matched_conditions: ["RSI(14) > 70"] },
    { symbol: "TITAN", company_name: "Titan Company", sector: "Consumer", ltp: 3250.80, change_pct: 1.45, volume: 1854200, rsi_14: 72.8, ema_status: "Bullish", matched_conditions: ["RSI(14) > 70"] },
    { symbol: "TRENT", company_name: "Trent Ltd", sector: "Retail", ltp: 5420.60, change_pct: 3.25, volume: 1245600, rsi_14: 81.5, ema_status: "Bullish", matched_conditions: ["RSI(14) > 70"] },
  ],
  volume_spike: [
    { symbol: "TATAMOTORS", company_name: "Tata Motors", sector: "Automobile", ltp: 745.90, change_pct: 3.45, volume: 25482100, rsi_14: 58.3, ema_status: "Bullish", matched_conditions: ["Volume > 2x Avg"] },
    { symbol: "SBIN", company_name: "State Bank of India", sector: "Banking", ltp: 812.45, change_pct: 1.85, volume: 19875420, rsi_14: 55.1, ema_status: "Bullish", matched_conditions: ["Volume > 2x Avg"] },
    { symbol: "RELIANCE", company_name: "Reliance Industries", sector: "Energy", ltp: 2945.50, change_pct: 2.12, volume: 17524610, rsi_14: 52.8, ema_status: "Bullish", matched_conditions: ["Volume > 2x Avg"] },
    { symbol: "ADANIENT", company_name: "Adani Enterprises", sector: "Conglomerate", ltp: 2450.80, change_pct: 4.52, volume: 15842300, rsi_14: 62.4, ema_status: "Bullish", matched_conditions: ["Volume > 2x Avg"] },
    { symbol: "JSWSTEEL", company_name: "JSW Steel", sector: "Metals", ltp: 845.20, change_pct: -1.85, volume: 14256800, rsi_14: 38.5, ema_status: "Bearish", matched_conditions: ["Volume > 2x Avg"] },
  ],
  bullish_ema_crossover: [
    { symbol: "TCS", company_name: "Tata Consultancy", sector: "IT", ltp: 3852.25, change_pct: 1.42, volume: 3215840, rsi_14: 56.8, ema_status: "Bullish", matched_conditions: ["EMA(9) > EMA(21)", "Bullish Cross"] },
    { symbol: "INFY", company_name: "Infosys", sector: "IT", ltp: 1628.30, change_pct: 0.96, volume: 6842150, rsi_14: 52.4, ema_status: "Bullish", matched_conditions: ["EMA(9) > EMA(21)", "Bullish Cross"] },
    { symbol: "HDFCBANK", company_name: "HDFC Bank", sector: "Banking", ltp: 1725.80, change_pct: 0.85, volume: 5124300, rsi_14: 54.2, ema_status: "Bullish", matched_conditions: ["EMA(9) > EMA(21)", "Bullish Cross"] },
    { symbol: "SUNPHARMA", company_name: "Sun Pharma", sector: "Pharma", ltp: 1585.40, change_pct: 1.15, volume: 2854600, rsi_14: 58.9, ema_status: "Bullish", matched_conditions: ["EMA(9) > EMA(21)", "Bullish Cross"] },
    { symbol: "MARUTI", company_name: "Maruti Suzuki", sector: "Automobile", ltp: 12080.50, change_pct: 0.72, volume: 845200, rsi_14: 51.6, ema_status: "Bullish", matched_conditions: ["EMA(9) > EMA(21)", "Bullish Cross"] },
  ],
  bearish_ema_crossover: [
    { symbol: "TATASTEEL", company_name: "Tata Steel", sector: "Metals", ltp: 128.40, change_pct: -2.15, volume: 18542300, rsi_14: 35.2, ema_status: "Bearish", matched_conditions: ["EMA(9) < EMA(21)", "Bearish Cross"] },
    { symbol: "HINDALCO", company_name: "Hindalco Industries", sector: "Metals", ltp: 485.60, change_pct: -1.45, volume: 7824500, rsi_14: 38.4, ema_status: "Bearish", matched_conditions: ["EMA(9) < EMA(21)", "Bearish Cross"] },
    { symbol: "WIPRO", company_name: "Wipro", sector: "IT", ltp: 462.75, change_pct: -1.82, volume: 5648210, rsi_14: 32.1, ema_status: "Bearish", matched_conditions: ["EMA(9) < EMA(21)", "Bearish Cross"] },
    { symbol: "INDUSINDBK", company_name: "IndusInd Bank", sector: "Banking", ltp: 1425.30, change_pct: -2.85, volume: 4215600, rsi_14: 30.5, ema_status: "Bearish", matched_conditions: ["EMA(9) < EMA(21)", "Bearish Cross"] },
    { symbol: "COALINDIA", company_name: "Coal India", sector: "Mining", ltp: 385.20, change_pct: -1.12, volume: 6542100, rsi_14: 36.8, ema_status: "Bearish", matched_conditions: ["EMA(9) < EMA(21)", "Bearish Cross"] },
  ],
  near_52_week_high: [
    { symbol: "BHARTIARTL", company_name: "Bharti Airtel", sector: "Telecom", ltp: 1542.30, change_pct: 1.85, volume: 3284500, rsi_14: 68.5, ema_status: "Bullish", matched_conditions: ["Within 5% of 52W High"] },
    { symbol: "BAJFINANCE", company_name: "Bajaj Finance", sector: "NBFC", ltp: 6890.50, change_pct: 2.12, volume: 2145800, rsi_14: 72.1, ema_status: "Bullish", matched_conditions: ["Within 5% of 52W High"] },
    { symbol: "TRENT", company_name: "Trent Ltd", sector: "Retail", ltp: 5420.60, change_pct: 3.25, volume: 1245600, rsi_14: 75.4, ema_status: "Bullish", matched_conditions: ["Within 5% of 52W High"] },
    { symbol: "ICICIBANK", company_name: "ICICI Bank", sector: "Banking", ltp: 1285.60, change_pct: 1.19, volume: 4521680, rsi_14: 65.8, ema_status: "Bullish", matched_conditions: ["Within 5% of 52W High"] },
    { symbol: "RELIANCE", company_name: "Reliance Industries", sector: "Energy", ltp: 2945.50, change_pct: 0.92, volume: 8524610, rsi_14: 62.3, ema_status: "Bullish", matched_conditions: ["Within 5% of 52W High"] },
  ],
  macd_bullish_cross: [
    { symbol: "SBIN", company_name: "State Bank of India", sector: "Banking", ltp: 812.45, change_pct: 1.25, volume: 9875420, rsi_14: 55.1, ema_status: "Bullish", matched_conditions: ["MACD > Signal", "Bullish Cross"] },
    { symbol: "TATAMOTORS", company_name: "Tata Motors", sector: "Automobile", ltp: 745.90, change_pct: 1.04, volume: 12548900, rsi_14: 52.3, ema_status: "Bullish", matched_conditions: ["MACD > Signal", "Bullish Cross"] },
    { symbol: "LT", company_name: "Larsen & Toubro", sector: "Infrastructure", ltp: 3425.80, change_pct: 0.65, volume: 2154800, rsi_14: 54.8, ema_status: "Bullish", matched_conditions: ["MACD > Signal", "Bullish Cross"] },
    { symbol: "NTPC", company_name: "NTPC Ltd", sector: "Power", ltp: 345.60, change_pct: 1.45, volume: 8524100, rsi_14: 58.2, ema_status: "Bullish", matched_conditions: ["MACD > Signal", "Bullish Cross"] },
    { symbol: "APOLLOHOSP", company_name: "Apollo Hospitals", sector: "Healthcare", ltp: 6280.40, change_pct: 0.85, volume: 542800, rsi_14: 56.4, ema_status: "Bullish", matched_conditions: ["MACD > Signal", "Bullish Cross"] },
  ],
  price_above_sma200: [
    { symbol: "RELIANCE", company_name: "Reliance Industries", sector: "Energy", ltp: 2945.50, change_pct: 0.92, volume: 8524610, rsi_14: 55.8, ema_status: "Bullish", matched_conditions: ["Price > SMA(200)"] },
    { symbol: "TCS", company_name: "Tata Consultancy", sector: "IT", ltp: 3852.25, change_pct: 0.62, volume: 3215840, rsi_14: 56.8, ema_status: "Bullish", matched_conditions: ["Price > SMA(200)"] },
    { symbol: "ICICIBANK", company_name: "ICICI Bank", sector: "Banking", ltp: 1285.60, change_pct: 1.19, volume: 4521680, rsi_14: 62.7, ema_status: "Bullish", matched_conditions: ["Price > SMA(200)"] },
    { symbol: "BHARTIARTL", company_name: "Bharti Airtel", sector: "Telecom", ltp: 1542.30, change_pct: 0.65, volume: 3284500, rsi_14: 58.9, ema_status: "Bullish", matched_conditions: ["Price > SMA(200)"] },
    { symbol: "BAJFINANCE", company_name: "Bajaj Finance", sector: "NBFC", ltp: 6890.50, change_pct: 1.95, volume: 2145800, rsi_14: 64.1, ema_status: "Bullish", matched_conditions: ["Price > SMA(200)"] },
  ],
  price_below_sma200: [
    { symbol: "TATASTEEL", company_name: "Tata Steel", sector: "Metals", ltp: 128.40, change_pct: -2.15, volume: 18542300, rsi_14: 32.4, ema_status: "Bearish", matched_conditions: ["Price < SMA(200)"] },
    { symbol: "WIPRO", company_name: "Wipro", sector: "IT", ltp: 462.75, change_pct: -1.82, volume: 5648210, rsi_14: 34.2, ema_status: "Bearish", matched_conditions: ["Price < SMA(200)"] },
    { symbol: "INDUSINDBK", company_name: "IndusInd Bank", sector: "Banking", ltp: 1425.30, change_pct: -2.85, volume: 4215600, rsi_14: 28.5, ema_status: "Bearish", matched_conditions: ["Price < SMA(200)"] },
    { symbol: "COALINDIA", company_name: "Coal India", sector: "Mining", ltp: 385.20, change_pct: -1.12, volume: 6542100, rsi_14: 36.8, ema_status: "Bearish", matched_conditions: ["Price < SMA(200)"] },
    { symbol: "BPCL", company_name: "Bharat Petroleum", sector: "Energy", ltp: 285.40, change_pct: -0.95, volume: 7842500, rsi_14: 38.2, ema_status: "Bearish", matched_conditions: ["Price < SMA(200)"] },
  ],
  bollinger_squeeze: [
    { symbol: "HDFCBANK", company_name: "HDFC Bank", sector: "Banking", ltp: 1725.80, change_pct: -0.12, volume: 5124300, rsi_14: 48.5, ema_status: "Neutral", matched_conditions: ["BB Width < 4%", "Squeeze"] },
    { symbol: "ITC", company_name: "ITC Ltd", sector: "FMCG", ltp: 445.60, change_pct: 0.08, volume: 9524100, rsi_14: 50.2, ema_status: "Neutral", matched_conditions: ["BB Width < 4%", "Squeeze"] },
    { symbol: "NESTLEIND", company_name: "Nestle India", sector: "FMCG", ltp: 2520.40, change_pct: -0.25, volume: 542800, rsi_14: 47.8, ema_status: "Neutral", matched_conditions: ["BB Width < 4%", "Squeeze"] },
    { symbol: "BRITANNIA", company_name: "Britannia Industries", sector: "FMCG", ltp: 5180.20, change_pct: 0.15, volume: 384500, rsi_14: 49.5, ema_status: "Neutral", matched_conditions: ["BB Width < 4%", "Squeeze"] },
    { symbol: "HINDUNILVR", company_name: "Hindustan Unilever", sector: "FMCG", ltp: 2385.60, change_pct: -0.18, volume: 1854200, rsi_14: 46.8, ema_status: "Neutral", matched_conditions: ["BB Width < 4%", "Squeeze"] },
  ],
  bullish_engulfing: [
    { symbol: "TATAMOTORS", company_name: "Tata Motors", sector: "Automobile", ltp: 745.90, change_pct: 2.85, volume: 12548900, rsi_14: 45.2, ema_status: "Bullish", matched_conditions: ["Bullish Engulfing"] },
    { symbol: "SBIN", company_name: "State Bank of India", sector: "Banking", ltp: 812.45, change_pct: 1.95, volume: 9875420, rsi_14: 42.8, ema_status: "Bullish", matched_conditions: ["Bullish Engulfing"] },
    { symbol: "LT", company_name: "Larsen & Toubro", sector: "Infrastructure", ltp: 3425.80, change_pct: 1.52, volume: 2154800, rsi_14: 48.2, ema_status: "Bullish", matched_conditions: ["Bullish Engulfing"] },
    { symbol: "DRREDDY", company_name: "Dr Reddy's Labs", sector: "Pharma", ltp: 5840.20, change_pct: 2.15, volume: 845600, rsi_14: 44.5, ema_status: "Bullish", matched_conditions: ["Bullish Engulfing"] },
    { symbol: "EICHERMOT", company_name: "Eicher Motors", sector: "Automobile", ltp: 4520.80, change_pct: 1.85, volume: 542100, rsi_14: 46.8, ema_status: "Bullish", matched_conditions: ["Bullish Engulfing"] },
  ],
  orb_breakout_long: [
    { symbol: "RELIANCE", company_name: "Reliance Industries", sector: "Energy", ltp: 2945.50, change_pct: 1.85, volume: 8524610, rsi_14: 58.4, ema_status: "Bullish", matched_conditions: ["Above ORB High"] },
    { symbol: "ICICIBANK", company_name: "ICICI Bank", sector: "Banking", ltp: 1285.60, change_pct: 1.62, volume: 4521680, rsi_14: 55.8, ema_status: "Bullish", matched_conditions: ["Above ORB High"] },
    { symbol: "TATAMOTORS", company_name: "Tata Motors", sector: "Automobile", ltp: 745.90, change_pct: 2.45, volume: 12548900, rsi_14: 52.1, ema_status: "Bullish", matched_conditions: ["Above ORB High"] },
    { symbol: "ADANIENT", company_name: "Adani Enterprises", sector: "Conglomerate", ltp: 2450.80, change_pct: 3.12, volume: 8542300, rsi_14: 60.5, ema_status: "Bullish", matched_conditions: ["Above ORB High"] },
    { symbol: "BAJFINANCE", company_name: "Bajaj Finance", sector: "NBFC", ltp: 6890.50, change_pct: 1.45, volume: 2145800, rsi_14: 62.8, ema_status: "Bullish", matched_conditions: ["Above ORB High"] },
  ],
};

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
