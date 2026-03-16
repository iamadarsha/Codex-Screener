"use client";

import Link from "next/link";
import { TrendingUp, Target, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";
import type { AiSuggestion } from "@/lib/api-types";

interface StockCardProps {
  suggestion: AiSuggestion;
  index: number;
  changePct?: number;
}

export function StockCard({ suggestion, index, changePct }: StockCardProps) {
  const confidence = suggestion.confidence ?? 0;
  // Normalize: if > 1, it's already a percentage (e.g. 80), otherwise multiply
  const confidenceNorm = confidence > 1 ? confidence : confidence * 100;
  const confidenceLabel =
    confidenceNorm >= 80 ? "High" : confidenceNorm >= 50 ? "Medium" : "Low";

  const hasChange = changePct != null;
  const changeColor = hasChange
    ? changePct >= 0 ? "text-bullish" : "text-bearish"
    : "text-text-muted";

  return (
    <Link
      href={`/chart/${suggestion.symbol}`}
      className="group block rounded-panel border border-border bg-card p-4 transition hover:border-accent/30 hover:shadow-lg"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-base font-bold text-text-primary group-hover:text-accent transition">
              {suggestion.symbol}
            </span>
            <Badge variant="accent" className="text-[10px]">
              #{index + 1}
            </Badge>
          </div>
          {suggestion.name && (
            <p className="mt-0.5 text-xs text-text-muted truncate max-w-[200px]">
              {suggestion.name}
            </p>
          )}
        </div>

        <div className="text-right">
          <div className={cn("text-sm font-bold tabular-nums", changeColor)}>
            {hasChange
              ? `${changePct >= 0 ? "+" : ""}${changePct.toFixed(1)}%`
              : "—"}
          </div>
          <div className="text-[10px] text-text-muted">{confidenceLabel}</div>
        </div>
      </div>

      {/* Rationale */}
      <p className="text-xs leading-relaxed text-text-secondary line-clamp-3 mb-3">
        {suggestion.rationale}
      </p>

      {/* Footer */}
      <div className="flex items-center gap-3 text-[10px] text-text-muted">
        {suggestion.entry_range && (
          <span className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            Entry: {suggestion.entry_range}
          </span>
        )}
        {suggestion.target && (
          <span className="flex items-center gap-1">
            <Target className="h-3 w-3" />
            Target: {suggestion.target}
          </span>
        )}
        {suggestion.stop_loss && (
          <span className="flex items-center gap-1">
            <ShieldAlert className="h-3 w-3" />
            SL: {suggestion.stop_loss}
          </span>
        )}
      </div>
    </Link>
  );
}
