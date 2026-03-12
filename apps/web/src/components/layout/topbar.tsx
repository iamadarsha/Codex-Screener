"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { LiveDot } from "@/components/ui/live-dot";
import { CountdownBar } from "@/components/ui/countdown-bar";
import { useMarketStatus, useMarketIndices } from "@/hooks/use-market-breadth";
import { formatPrice, formatPercent } from "@/lib/format";
import { cn } from "@/lib/cn";

export function Topbar() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const { data: status } = useMarketStatus();
  const { data: indices } = useMarketIndices();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (search.trim()) {
      router.push(`/chart/${search.trim().toUpperCase()}`);
      setSearch("");
    }
  };

  return (
    <header className="flex flex-col border-b border-[#191a22] bg-[rgba(14,15,20,0.72)] backdrop-blur">
      <div className="flex h-14 items-center justify-between px-6">
        {/* Index tickers */}
        <div className="flex items-center gap-6">
          {indices?.slice(0, 3).map((idx) => (
            <div key={idx.symbol} className="flex items-center gap-2">
              <span className="text-xs font-medium text-[#8B8D9A]">
                {idx.symbol}
              </span>
              <span className="font-mono text-sm text-white">
                {formatPrice(idx.value)}
              </span>
              <span
                className={cn(
                  "font-mono text-xs",
                  idx.change_pct >= 0 ? "text-[#00C896]" : "text-[#FF4757]"
                )}
              >
                {formatPercent(idx.change_pct)}
              </span>
            </div>
          )) ?? (
            <div className="text-sm text-[#8B8D9A]">Loading indices...</div>
          )}
        </div>

        <div className="flex items-center gap-4">
          {/* Search */}
          <form onSubmit={handleSearch} className="relative">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#5C5D6E]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search symbol..."
              className="h-9 w-48 rounded-lg border border-[#2A2B35] bg-[#13141A] pl-9 pr-3 text-sm text-[#E8E9F0] placeholder-[#5C5D6E] outline-none transition focus:w-64 focus:border-[#7C5CFC]"
            />
          </form>

          {/* Live indicator */}
          <div className="flex items-center gap-2 rounded-full border border-[#1E1F28] bg-[#13141A] px-3 py-1.5">
            <LiveDot color={status?.is_open ? "green" : "red"} />
            <span
              className={cn(
                "text-xs font-semibold uppercase tracking-[0.2em]",
                status?.is_open ? "text-[#00C896]" : "text-[#FF4757]"
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
