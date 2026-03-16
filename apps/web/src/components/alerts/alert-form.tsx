"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BellPlus, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { fetchStocks } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { AlertCreateRequest } from "@/lib/api-types";

interface AlertFormProps {
  onSubmit: (req: AlertCreateRequest) => void;
  isLoading?: boolean;
}

const CONDITIONS = [
  { value: "price_above", label: "Price Above" },
  { value: "price_below", label: "Price Below" },
  { value: "change_pct_above", label: "Change % Above" },
  { value: "change_pct_below", label: "Change % Below" },
  { value: "volume_above", label: "Volume Above" },
  { value: "rsi_above", label: "RSI Above" },
  { value: "rsi_below", label: "RSI Below" },
];

const OPERATORS = [
  { value: "gt", label: "Greater Than" },
  { value: "lt", label: "Less Than" },
  { value: "gte", label: "Greater or Equal" },
  { value: "lte", label: "Less or Equal" },
];

export function AlertForm({ onSubmit, isLoading }: AlertFormProps) {
  const [symbolSearch, setSymbolSearch] = useState("");
  const [selectedSymbol, setSelectedSymbol] = useState("");
  const [conditionType, setConditionType] = useState("price_above");
  const [operator, setOperator] = useState("gt");
  const [conditionValue, setConditionValue] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);

  const { data: searchData } = useQuery({
    queryKey: ["alert-stock-search", symbolSearch],
    queryFn: () => fetchStocks({ search: symbolSearch, limit: 8 }),
    enabled: symbolSearch.length >= 1 && showDropdown,
  });

  const selectClass = cn(
    "h-10 rounded-lg border border-border bg-page px-3 text-sm text-text-primary outline-none transition",
    "focus:border-accent hover:border-border"
  );

  const handleSubmit = () => {
    if (!selectedSymbol || !conditionValue) return;
    onSubmit({
      symbol: selectedSymbol,
      condition_type: conditionType,
      condition_value: Number(conditionValue),
      operator,
    });
    setSelectedSymbol("");
    setSymbolSearch("");
    setConditionValue("");
  };

  return (
    <div className="rounded-panel border border-border bg-card p-5">
      <div className="mb-4 flex items-center gap-2">
        <BellPlus className="h-4 w-4 text-accent" />
        <h3 className="text-sm font-semibold text-text-primary">Create Alert</h3>
      </div>

      <div className="space-y-4">
        {/* Symbol selector */}
        <div className="relative">
          <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-text-secondary">
            Symbol
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              value={selectedSymbol || symbolSearch}
              onChange={(e) => {
                setSymbolSearch(e.target.value);
                setSelectedSymbol("");
                setShowDropdown(true);
              }}
              onFocus={() => setShowDropdown(true)}
              placeholder="Search symbol..."
              className="h-10 w-full rounded-lg border border-border bg-page pl-9 pr-3 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent"
            />
          </div>
          {showDropdown && searchData?.stocks && searchData.stocks.length > 0 && !selectedSymbol && (
            <div className="absolute z-10 mt-1 w-full rounded-lg border border-border bg-card py-1 shadow-lg">
              {searchData.stocks.map((s) => (
                <button
                  key={s.symbol}
                  onClick={() => {
                    setSelectedSymbol(s.symbol);
                    setSymbolSearch("");
                    setShowDropdown(false);
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-elevated"
                >
                  <span className="font-mono font-semibold text-text-primary">
                    {s.symbol}
                  </span>
                  <span className="text-xs text-text-secondary">{s.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-text-secondary">
              Condition
            </label>
            <select
              value={conditionType}
              onChange={(e) => setConditionType(e.target.value)}
              className={cn(selectClass, "w-full")}
            >
              {CONDITIONS.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-text-secondary">
              Operator
            </label>
            <select
              value={operator}
              onChange={(e) => setOperator(e.target.value)}
              className={cn(selectClass, "w-full")}
            >
              {OPERATORS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <Input
          label="Value"
          type="number"
          value={conditionValue}
          onChange={(e) => setConditionValue(e.target.value)}
          placeholder="Enter threshold value"
        />

        <Button
          onClick={handleSubmit}
          disabled={!selectedSymbol || !conditionValue || isLoading}
          className="w-full"
        >
          {isLoading ? "Creating..." : "Create Alert"}
        </Button>
      </div>
    </div>
  );
}
