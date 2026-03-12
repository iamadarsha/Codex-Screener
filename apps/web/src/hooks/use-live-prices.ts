"use client";

import { useEffect, useRef } from "react";
import { priceSocket } from "@/lib/socket";
import { useLivePriceStore } from "@/store/live-price-store";
import type { LivePrice } from "@/lib/api-types";

/**
 * Hook that subscribes to real-time price updates for the given symbols.
 * Returns a map of symbol -> LivePrice.
 */
export function useLivePrices(symbols: string[]) {
  const updatePrice = useLivePriceStore((s) => s.updatePrice);
  const prices = useLivePriceStore((s) => s.prices);
  const prevSymbolsRef = useRef<string[]>([]);

  useEffect(() => {
    const prev = prevSymbolsRef.current;
    const toSub = symbols.filter((s) => !prev.includes(s));
    const toUnsub = prev.filter((s) => !symbols.includes(s));

    if (toSub.length > 0) {
      priceSocket.subscribe(toSub);
    }
    if (toUnsub.length > 0) {
      priceSocket.unsubscribe(toUnsub);
    }

    prevSymbolsRef.current = symbols;
  }, [symbols]);

  useEffect(() => {
    const unsub = priceSocket.onPrice((price: LivePrice) => {
      updatePrice(price);
    });
    priceSocket.connect();
    return unsub;
  }, [updatePrice]);

  const result: Record<string, LivePrice> = {};
  for (const s of symbols) {
    if (prices[s]) result[s] = prices[s];
  }
  return result;
}
