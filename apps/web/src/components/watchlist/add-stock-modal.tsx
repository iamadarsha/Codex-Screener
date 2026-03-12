"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Plus } from "lucide-react";
import { Modal } from "@/components/ui/modal";
import { fetchStocks } from "@/lib/api";
import { cn } from "@/lib/cn";

interface AddStockModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (symbol: string) => void;
  existingSymbols: string[];
}

export function AddStockModal({
  open,
  onClose,
  onAdd,
  existingSymbols,
}: AddStockModalProps) {
  const [search, setSearch] = useState("");

  const { data } = useQuery({
    queryKey: ["stocks-search", search],
    queryFn: () => fetchStocks({ search, limit: 20 }),
    enabled: open && search.length >= 1,
  });

  const stocks = data?.stocks ?? [];

  return (
    <Modal open={open} onClose={onClose} title="Add Stock to Watchlist">
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#5C5D6E]" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by symbol or name..."
          autoFocus
          className="h-10 w-full rounded-lg border border-[#2A2B35] bg-[#13141A] pl-10 pr-3 text-sm text-[#E8E9F0] placeholder-[#5C5D6E] outline-none focus:border-[#7C5CFC]"
        />
      </div>

      <div className="max-h-64 overflow-y-auto">
        {stocks.map((stock) => {
          const isAdded = existingSymbols.includes(stock.symbol);
          return (
            <button
              key={stock.symbol}
              disabled={isAdded}
              onClick={() => {
                onAdd(stock.symbol);
                onClose();
              }}
              className={cn(
                "flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left transition",
                isAdded
                  ? "cursor-not-allowed opacity-40"
                  : "hover:bg-[#22232D]"
              )}
            >
              <div>
                <span className="font-mono text-sm font-semibold text-white">
                  {stock.symbol}
                </span>
                <div className="text-xs text-[#8B8D9A]">{stock.name}</div>
              </div>
              {isAdded ? (
                <span className="text-xs text-[#5C5D6E]">Added</span>
              ) : (
                <Plus className="h-4 w-4 text-[#7C5CFC]" />
              )}
            </button>
          );
        })}
        {search.length >= 1 && stocks.length === 0 && (
          <div className="py-8 text-center text-sm text-[#5C5D6E]">
            No stocks found
          </div>
        )}
        {search.length === 0 && (
          <div className="py-8 text-center text-sm text-[#5C5D6E]">
            Type to search for stocks
          </div>
        )}
      </div>
    </Modal>
  );
}
