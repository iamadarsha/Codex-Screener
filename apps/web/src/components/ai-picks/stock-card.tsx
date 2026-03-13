"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  ChevronUp,
  Target,
  TrendingUp,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/cn";
import type { AiSuggestion } from "@/lib/api-types";

const horizonColors: Record<string, string> = {
  intraday: "text-[#f59e0b] bg-[#f59e0b]/10",
  swing: "text-[#7c5cfc] bg-[#7c5cfc]/10",
  positional: "text-[#00c796] bg-[#00c796]/10",
};

const confidenceColor = (c: number) =>
  c >= 8 ? "text-[#00c796]" : c >= 6 ? "text-[#f59e0b]" : "text-[#ff5a8a]";

const confidenceBarGradient = (c: number) => {
  const pct = (c / 10) * 100;
  return `linear-gradient(90deg, #ff5a8a 0%, #f59e0b 50%, #00c796 100%)`;
};

interface StockCardProps {
  suggestion: AiSuggestion;
  index: number;
}

export function StockCard({ suggestion, index }: StockCardProps) {
  const [expanded, setExpanded] = useState(false);
  const confidencePct = (suggestion.confidence / 10) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.3 }}
      className={cn(
        "card-hover rounded-panel border border-border bg-card p-5 shadow-card cursor-pointer"
      )}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-base font-semibold text-white">
              {suggestion.symbol}
            </span>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase",
                horizonColors[suggestion.target_horizon] ??
                  "text-[#8b95a8] bg-[#1c2333]"
              )}
            >
              {suggestion.target_horizon}
            </span>
            {suggestion.action && (
              <span
                className={cn(
                  "rounded px-1.5 py-0.5 text-[10px] font-bold uppercase",
                  suggestion.action === "BUY"
                    ? "bg-[#00c796]/15 text-[#00c796]"
                    : "bg-[#ff5a8a]/15 text-[#ff5a8a]"
                )}
              >
                {suggestion.action}
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-[#8b95a8]">{suggestion.name}</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <Target className="h-3.5 w-3.5 text-[#5a6478]" />
            <span
              className={cn(
                "text-sm font-bold",
                confidenceColor(suggestion.confidence)
              )}
            >
              {suggestion.confidence}/10
            </span>
          </div>
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-[#5a6478]" />
          ) : (
            <ChevronDown className="h-4 w-4 text-[#5a6478]" />
          )}
        </div>
      </div>

      {/* Confidence bar */}
      <div className="mt-3">
        <div className="h-1.5 w-full rounded-full bg-[#1c2333] overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${confidencePct}%`,
              background: confidenceBarGradient(suggestion.confidence),
            }}
          />
        </div>
      </div>

      {/* Target & Stop loss */}
      {(suggestion.target_pct != null || suggestion.stop_loss_pct != null) && (
        <div className="mt-2 flex items-center gap-3 text-[11px]">
          {suggestion.target_pct != null && (
            <span className="text-[#00c796]">
              Target: +{suggestion.target_pct}%
            </span>
          )}
          {suggestion.stop_loss_pct != null && (
            <span className="text-[#ff5a8a]">
              SL: -{suggestion.stop_loss_pct}%
            </span>
          )}
        </div>
      )}

      {/* Sector badge + tags */}
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <span className="rounded bg-[#1c2333] px-2 py-0.5 text-[10px] text-[#8b95a8]">
          {suggestion.sector}
        </span>
        {suggestion.tags?.map((tag) => (
          <span
            key={tag}
            className="rounded bg-[#7c5cfc]/10 px-2 py-0.5 text-[10px] font-medium text-[#7c5cfc]"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Expandable content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-4 space-y-3 border-t border-border pt-4">
              <div className="flex items-start gap-2">
                <TrendingUp className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#7c5cfc]" />
                <p className="text-xs leading-relaxed text-[#c8cdd8]">
                  {suggestion.rationale}
                </p>
              </div>
              <div className="flex items-start gap-2">
                <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#f59e0b]" />
                <p className="text-xs text-[#c8cdd8]">
                  <span className="font-medium text-white">Catalyst:</span>{" "}
                  {suggestion.catalyst}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
