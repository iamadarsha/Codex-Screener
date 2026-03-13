"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { Bell, Search, Sun, Moon } from "lucide-react";
import { useRouter } from "next/navigation";
import { LiveDot } from "@/components/ui/live-dot";
import { CountdownBar } from "@/components/ui/countdown-bar";
import { useMarketStatus, useMarketIndices } from "@/hooks/use-market-breadth";
import { formatPrice, formatPercent } from "@/lib/format";
import { cn } from "@/lib/cn";
import { useTheme } from "@/components/providers/theme-provider";
import { fetchStocks } from "@/lib/api";
import type { Stock } from "@/lib/api-types";

function useIsMarketLive(): boolean {
  const [live, setLive] = useState(false);

  useEffect(() => {
    function check() {
      const now = new Date();
      // Convert to IST (UTC+5:30)
      const utc = now.getTime() + now.getTimezoneOffset() * 60000;
      const ist = new Date(utc + 5.5 * 3600000);
      const day = ist.getDay(); // 0=Sun,6=Sat
      const hours = ist.getHours();
      const mins = ist.getMinutes();
      const totalMins = hours * 60 + mins;
      // Weekday 9:15 - 15:30 IST
      const isWeekday = day >= 1 && day <= 5;
      const inHours = totalMins >= 9 * 60 + 15 && totalMins <= 15 * 60 + 30;
      setLive(isWeekday && inHours);
    }
    check();
    const interval = setInterval(check, 60_000);
    return () => clearInterval(interval);
  }, []);

  return live;
}

function IndexTicker({
  name,
  last,
  changePct,
}: {
  name: string;
  last: number;
  changePct: number;
}) {
  const prevRef = useRef(last);
  const [flash, setFlash] = useState<"up" | "down" | null>(null);

  useEffect(() => {
    if (last > prevRef.current) setFlash("up");
    else if (last < prevRef.current) setFlash("down");
    prevRef.current = last;
    const t = setTimeout(() => setFlash(null), 600);
    return () => clearTimeout(t);
  }, [last]);

  return (
    <div className="flex shrink-0 items-center gap-2 px-1">
      <span className="text-[11px] font-medium text-text-muted">{name}</span>
      <span
        className={cn(
          "font-mono text-sm tabular-nums text-text-primary transition-colors",
          flash === "up" && "flash-bullish",
          flash === "down" && "flash-bearish"
        )}
      >
        {formatPrice(last)}
      </span>
      <span
        className={cn(
          "font-mono text-xs tabular-nums",
          changePct >= 0 ? "text-bullish" : "text-bearish"
        )}
      >
        {formatPercent(changePct)}
      </span>
    </div>
  );
}

export function Topbar() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [suggestions, setSuggestions] = useState<Stock[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const { data: status } = useMarketStatus();
  const { data: indices } = useMarketIndices();
  const isMarketLive = useIsMarketLive();
  const { theme, toggleTheme } = useTheme();

  const searchStocks = useCallback((query: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.length < 1) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetchStocks({ search: query, limit: 8 });
        setSuggestions(res.stocks ?? []);
        setShowDropdown(true);
        setSelectedIdx(-1);
      } catch {
        setSuggestions([]);
      }
    }, 250);
  }, []);

  const navigateToChart = useCallback(
    (symbol: string) => {
      router.push(`/chart/${symbol.toUpperCase()}`);
      setSearch("");
      setSuggestions([]);
      setShowDropdown(false);
    },
    [router]
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedIdx >= 0 && suggestions[selectedIdx]) {
      navigateToChart(suggestions[selectedIdx].symbol);
    } else if (search.trim()) {
      navigateToChart(search.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || suggestions.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIdx((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIdx((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === "Escape") {
      setShowDropdown(false);
    }
  };

  return (
    <header className="glass-topbar flex flex-col">
      <div className="flex h-14 items-center justify-between gap-4 px-6">
        {/* Scrollable index tickers */}
        <div className="flex flex-1 items-center gap-5 overflow-x-auto scrollbar-none">
          {indices?.slice(0, 5).map((idx) => (
            <IndexTicker
              key={idx.symbol}
              name={idx.name ?? idx.symbol}
              last={idx.last ?? idx.value}
              changePct={idx.change_pct}
            />
          )) ?? (
            <div className="text-sm text-text-muted">Loading indices...</div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Search with autocomplete */}
          <div className="relative" ref={dropdownRef}>
            <form onSubmit={handleSearch}>
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-muted z-10" />
              <input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  searchStocks(e.target.value);
                }}
                onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                onKeyDown={handleKeyDown}
                placeholder="Search symbol..."
                className="h-9 w-48 rounded-lg border border-border bg-card pl-9 pr-14 text-sm text-text-primary placeholder-text-muted outline-none transition focus:w-64 focus:border-accent"
              />
              <kbd className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded border border-border bg-page px-1.5 py-0.5 text-[10px] text-text-muted">
                ⌘K
              </kbd>
            </form>
            {showDropdown && suggestions.length > 0 && (
              <div className="absolute right-0 top-full z-50 mt-1 w-72 overflow-hidden rounded-lg border border-border bg-elevated shadow-lg backdrop-blur-xl">
                {suggestions.map((stock, i) => (
                  <button
                    key={stock.symbol}
                    type="button"
                    onMouseDown={() => navigateToChart(stock.symbol)}
                    className={cn(
                      "flex w-full items-center gap-3 px-3 py-2 text-left text-sm transition hover:bg-card",
                      i === selectedIdx && "bg-card"
                    )}
                  >
                    <span className="font-mono font-semibold text-accent">
                      {stock.symbol}
                    </span>
                    <span className="truncate text-text-secondary">
                      {stock.name}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="rounded-lg p-2 text-text-secondary transition hover:bg-elevated hover:text-text-primary"
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </button>

          {/* Live market indicator */}
          {isMarketLive && (
            <div className="flex items-center gap-1.5 rounded-full border border-bullish/20 bg-bullish/5 px-2.5 py-1">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-bullish opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-bullish" />
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-bullish">
                LIVE
              </span>
            </div>
          )}

          {/* Notification bell */}
          <button className="relative rounded-lg p-2 text-text-secondary transition hover:bg-elevated hover:text-text-primary">
            <Bell className="h-4 w-4" />
            <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-bearish" />
          </button>

          {/* Live indicator */}
          <div className="flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5">
            <LiveDot color={status?.is_open ? "green" : "red"} />
            <span
              className={cn(
                "text-[10px] font-semibold uppercase tracking-[0.15em]",
                status?.is_open ? "text-bullish" : "text-bearish"
              )}
            >
              {status?.is_open ? "Live" : "Closed"}
            </span>
          </div>
        </div>
      </div>

      {/* Market countdown bar */}
      <div className="px-6 pb-2">
        <CountdownBar isOpen={status?.is_open ?? false} />
      </div>
    </header>
  );
}
