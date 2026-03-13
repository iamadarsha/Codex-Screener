"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { formatPrice } from "@/lib/format";

interface PriceCellProps {
  price: number;
  previousPrice?: number;
  className?: string;
}

export function PriceCell({ price, previousPrice, className }: PriceCellProps) {
  const [flash, setFlash] = useState<"up" | "down" | null>(null);
  const prevRef = useRef(price);

  useEffect(() => {
    const prev = previousPrice ?? prevRef.current;
    if (price > prev) {
      setFlash("up");
    } else if (price < prev) {
      setFlash("down");
    }
    prevRef.current = price;

    const timer = setTimeout(() => setFlash(null), 600);
    return () => clearTimeout(timer);
  }, [price, previousPrice]);

  return (
    <span
      className={cn(
        "inline-block rounded px-1 font-mono tabular-nums transition-colors duration-300",
        flash === "up" && "flash-bullish text-bullish",
        flash === "down" && "flash-bearish text-bearish",
        !flash && "text-text-primary",
        className
      )}
    >
      {formatPrice(price)}
    </span>
  );
}
