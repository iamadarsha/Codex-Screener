"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Bell, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { LiveDot } from "@/components/ui/live-dot";
import { CountdownBar } from "@/components/ui/countdown-bar";
import { useMarketStatus, useMarketIndices } from "@/hooks/use-market-breadth";
import { formatPrice, formatPercent } from "@/lib/format";
import { cn } from "@/lib/cn";

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
      <span className="text-[11px] font-medium text-[#5a6478]">{name}</span>
      <span
        className={cn(
          "font-mono text-sm tabular-nums text-white transition-colors",
          flash === "up" && "flash-bullish",
          flash === "down" && "flash-bearish"
        )}
      >
        {formatPrice(last)}
      </span>
      <span
        className={cn(
          "font-mono text-xs tabular-nums",
          changePct >= 0 ? "text-[#00c796]" : "text-[#ff5a8a]"
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
  const { data: status } = useMarketStatus();
  const { data: indices } = useMarketIndices();
  const isMarketLive = useIsMarketLive();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (search.trim()) {
      router.push(`/chart/${search.trim().toUpperCase()}`);
      setSearch("");
    }
  };

  return (
    <header className="flex flex-col border-b border-[#1a2235] bg-[rgba(10,14,26,0.8)] backdrop-blur-md">
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
            <div className="text-sm text-[#5a6478]">Loading indices...</div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Search */}
          <form onSubmit={handleSearch} className="relative">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#5a6478]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search symbol..."
              className="h-9 w-48 rounded-lg border border-[#232d40] bg-[#101624] pl-9 pr-14 text-sm text-[#e8ecf4] placeholder-[#5a6478] outline-none transition focus:w-64 focus:border-[#7c5cfc]"
            />
            <kbd className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded border border-[#232d40] bg-[#0a0e1a] px-1.5 py-0.5 text-[10px] text-[#5a6478]">
              ⌘K
            </kbd>
          </form>

          {/* Live market indicator */}
          {isMarketLive && (
            <div className="flex items-center gap-1.5 rounded-full border border-[#00c796]/20 bg-[#00c796]/5 px-2.5 py-1">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#00c796] opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[#00c796]" />
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#00c796]">
                LIVE
              </span>
            </div>
          )}

          {/* Notification bell */}
          <button className="relative rounded-lg p-2 text-[#5a6478] transition hover:bg-[#1c2333] hover:text-white">
            <Bell className="h-4 w-4" />
            <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-[#ff5a8a]" />
          </button>

          {/* Live indicator */}
          <div className="flex items-center gap-2 rounded-full border border-[#232d40] bg-[#101624] px-3 py-1.5">
            <LiveDot color={status?.is_open ? "green" : "red"} />
            <span
              className={cn(
                "text-[10px] font-semibold uppercase tracking-[0.15em]",
                status?.is_open ? "text-[#00c796]" : "text-[#ff5a8a]"
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
