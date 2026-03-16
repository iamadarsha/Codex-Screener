"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { haptic } from "@/lib/haptic";

interface PullToRefreshOptions {
  onRefresh: () => Promise<void>;
  threshold?: number;
  maxPull?: number;
}

interface PullToRefreshState {
  pulling: boolean;
  pullDistance: number;
  refreshing: boolean;
}

export function usePullToRefresh({
  onRefresh,
  threshold = 80,
  maxPull = 120,
}: PullToRefreshOptions): PullToRefreshState & {
  containerRef: React.RefObject<HTMLDivElement | null>;
} {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const startY = useRef(0);
  const [pulling, setPulling] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const triggeredRef = useRef(false);

  const handleTouchStart = useCallback((e: TouchEvent) => {
    // Only start pull-to-refresh if scrolled to top
    if (window.scrollY > 5) return;
    startY.current = e.touches[0].clientY;
    setPulling(true);
    triggeredRef.current = false;
  }, []);

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (!pulling || refreshing) return;
      const currentY = e.touches[0].clientY;
      const diff = Math.max(0, currentY - startY.current);
      // Apply resistance (logarithmic feel)
      const dampened = Math.min(maxPull, diff * 0.5);
      setPullDistance(dampened);

      // Haptic when crossing threshold
      if (dampened >= threshold && !triggeredRef.current) {
        triggeredRef.current = true;
        haptic("medium");
      } else if (dampened < threshold && triggeredRef.current) {
        triggeredRef.current = false;
      }

      if (diff > 10) {
        e.preventDefault();
      }
    },
    [pulling, refreshing, threshold, maxPull]
  );

  const handleTouchEnd = useCallback(async () => {
    if (!pulling) return;
    setPulling(false);

    if (pullDistance >= threshold && !refreshing) {
      setRefreshing(true);
      haptic("heavy");
      try {
        await onRefresh();
      } finally {
        setRefreshing(false);
      }
    }
    setPullDistance(0);
  }, [pulling, pullDistance, threshold, refreshing, onRefresh]);

  useEffect(() => {
    const el = containerRef.current ?? document;
    el.addEventListener("touchstart", handleTouchStart as EventListener, { passive: true });
    el.addEventListener("touchmove", handleTouchMove as EventListener, { passive: false });
    el.addEventListener("touchend", handleTouchEnd as EventListener, { passive: true });
    return () => {
      el.removeEventListener("touchstart", handleTouchStart as EventListener);
      el.removeEventListener("touchmove", handleTouchMove as EventListener);
      el.removeEventListener("touchend", handleTouchEnd as EventListener);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  return { pulling, pullDistance, refreshing, containerRef };
}
