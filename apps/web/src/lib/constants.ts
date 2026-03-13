export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8001";

export const WS_PRICES_URL = `${WS_BASE_URL}/ws/prices`;

export const DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001";

export const TIMEFRAME_OPTIONS = [
  { label: "1m", value: "1min" },
  { label: "5m", value: "5min" },
  { label: "15m", value: "15min" },
  { label: "1D", value: "daily" },
] as const;

export type Timeframe = (typeof TIMEFRAME_OPTIONS)[number]["value"];

export const INDICATOR_OPTIONS = [
  { label: "EMA 20", value: "ema20" },
  { label: "EMA 50", value: "ema50" },
  { label: "RSI", value: "rsi" },
  { label: "MACD", value: "macd" },
  { label: "Bollinger Bands", value: "bb" },
] as const;

export const SECTORS = [
  "IT",
  "Banking",
  "Pharma",
  "Auto",
  "FMCG",
  "Energy",
  "Metal",
  "Realty",
  "Infra",
  "Media",
  "Telecom",
  "Financial Services",
] as const;

export const REFETCH_INTERVAL = 30_000;
export const LIVE_REFETCH_INTERVAL = 5_000;
