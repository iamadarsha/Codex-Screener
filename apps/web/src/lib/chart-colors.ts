export const CHART_COLORS = {
  background: "#0E0F14",
  grid: "#1E1F28",
  crosshair: "#7C5CFC",
  text: "#8B8D9A",
  textBold: "#E8E9F0",

  bullishCandle: "#00C896",
  bearishCandle: "#FF4757",
  bullishWick: "#00C896",
  bearishWick: "#FF4757",

  volume: "rgba(124, 92, 252, 0.3)",
  volumeUp: "rgba(0, 200, 150, 0.4)",
  volumeDown: "rgba(255, 71, 87, 0.4)",

  ema20: "#7C5CFC",
  ema50: "#FFA502",
  rsi: "#2ED9FF",
  macd: "#00C896",
  macdSignal: "#FF4757",
  macdHistogram: "rgba(124, 92, 252, 0.5)",
  bbUpper: "rgba(124, 92, 252, 0.4)",
  bbLower: "rgba(124, 92, 252, 0.4)",
  bbMiddle: "#7C5CFC",

  sectorPositive: "#00C896",
  sectorNegative: "#FF4757",
  sectorNeutral: "#2A2B35",

  donutAdvance: "#00C896",
  donutDecline: "#FF4757",
  donutUnchanged: "#2A2B35",
} as const;

export const SECTOR_HEATMAP_SCALE = [
  { min: -Infinity, max: -3, color: "#D32F2F" },
  { min: -3, max: -1, color: "#FF4757" },
  { min: -1, max: 0, color: "#FF8A80" },
  { min: 0, max: 1, color: "#80CBC4" },
  { min: 1, max: 3, color: "#00C896" },
  { min: 3, max: Infinity, color: "#00897B" },
] as const;
