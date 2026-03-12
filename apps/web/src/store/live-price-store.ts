import { create } from "zustand";
import type { LivePrice } from "@/lib/api-types";

interface LivePriceState {
  prices: Record<string, LivePrice>;
  /** Previous prices for flash-on-change detection */
  previousPrices: Record<string, number>;
  updatePrice: (price: LivePrice) => void;
  updatePrices: (prices: LivePrice[]) => void;
  getPrice: (symbol: string) => LivePrice | undefined;
  getChange: (symbol: string) => "up" | "down" | "none";
}

export const useLivePriceStore = create<LivePriceState>((set, get) => ({
  prices: {},
  previousPrices: {},

  updatePrice: (price: LivePrice) => {
    set((state) => {
      const prev = state.prices[price.symbol]?.ltp;
      return {
        prices: { ...state.prices, [price.symbol]: price },
        previousPrices: prev !== undefined
          ? { ...state.previousPrices, [price.symbol]: prev }
          : state.previousPrices,
      };
    });
  },

  updatePrices: (prices: LivePrice[]) => {
    set((state) => {
      const newPrices = { ...state.prices };
      const newPrevPrices = { ...state.previousPrices };
      for (const p of prices) {
        const prev = state.prices[p.symbol]?.ltp;
        if (prev !== undefined) {
          newPrevPrices[p.symbol] = prev;
        }
        newPrices[p.symbol] = p;
      }
      return { prices: newPrices, previousPrices: newPrevPrices };
    });
  },

  getPrice: (symbol: string) => get().prices[symbol],

  getChange: (symbol: string) => {
    const current = get().prices[symbol]?.ltp;
    const previous = get().previousPrices[symbol];
    if (current === undefined || previous === undefined) return "none";
    if (current > previous) return "up";
    if (current < previous) return "down";
    return "none";
  },
}));
