"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";

interface AnimatedNumberProps {
  value: number;
  format?: (v: number) => string;
  className?: string;
  duration?: number;
}

export function AnimatedNumber({
  value,
  format = (v) => v.toFixed(2),
  className,
  duration = 400,
}: AnimatedNumberProps) {
  const [display, setDisplay] = useState(value);
  const prevRef = useRef(value);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    const from = prevRef.current;
    const to = value;
    if (from === to) return;

    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setDisplay(from + (to - from) * eased);
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      } else {
        prevRef.current = to;
      }
    };
    frameRef.current = requestAnimationFrame(animate);

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [value, duration]);

  return (
    <span className={cn("font-mono tabular-nums", className)}>
      {format(display)}
    </span>
  );
}
