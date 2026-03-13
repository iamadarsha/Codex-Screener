"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  ChevronUp,
  Target,
  TrendingUp,
  Sparkles,
  Info,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/cn";
import type { AiSuggestion } from "@/lib/api-types";

const horizonColors: Record<string, string> = {
  intraday: "text-warning bg-warning/10",
  swing: "text-accent bg-accent/10",
  positional: "text-bullish bg-bullish/10",
};

const confidenceColor = (c: number) =>
  c >= 8 ? "text-bullish" : c >= 6 ? "text-warning" : "text-bearish";

const confidenceBarGradient = (_c: number) => {
  return `linear-gradient(90deg, var(--bearish) 0%, var(--warning) 50%, var(--bullish) 100%)`;
};

interface StockCardProps {
  suggestion: AiSuggestion;
  index: number;
}

export function StockCard({ suggestion, index }: StockCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const sourcesRef = useRef<HTMLDivElement>(null);
  const confidencePct = (suggestion.confidence / 10) * 100;

  useEffect(() => {
    if (!showSources) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (sourcesRef.current && !sourcesRef.current.contains(e.target as Node)) {
        setShowSources(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showSources]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.3 }}
      className={cn(
        "card-hover rounded-panel border border-border bg-card p-5 shadow-card cursor-pointer relative"
      )}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-base font-semibold text-text-primary">
              {suggestion.symbol}
            </span>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase",
                horizonColors[suggestion.target_horizon] ??
                  "text-text-secondary bg-elevated"
              )}
            >
              {suggestion.target_horizon}
            </span>
            {suggestion.action && (
              <span
                className={cn(
                  "rounded px-1.5 py-0.5 text-[10px] font-bold uppercase",
                  suggestion.action === "BUY"
                    ? "bg-bullish/15 text-bullish"
                    : "bg-bearish/15 text-bearish"
                )}
              >
                {suggestion.action}
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-text-secondary">{suggestion.name}</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Info button */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setShowSources(!showSources);
            }}
            className="rounded-md p-1 text-text-muted transition hover:bg-elevated hover:text-accent"
            title="View news sources"
          >
            <Info className="h-3.5 w-3.5" />
          </button>
          <div className="flex items-center gap-1">
            <Target className="h-3.5 w-3.5 text-text-muted" />
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
            <ChevronUp className="h-4 w-4 text-text-muted" />
          ) : (
            <ChevronDown className="h-4 w-4 text-text-muted" />
          )}
        </div>
      </div>

      {/* News Sources Popover */}
      {showSources && (
        <div
          ref={sourcesRef}
          className="absolute left-0 right-0 top-12 z-50 mx-2 rounded-lg border border-border bg-elevated p-4 shadow-lg backdrop-blur-xl sm:left-auto sm:right-4 sm:mx-0 sm:w-80"
          onClick={(e) => e.stopPropagation()}
        >
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
            News Sources
          </h4>
          {suggestion.news_sources && suggestion.news_sources.length > 0 ? (
            <div className="space-y-2">
              {suggestion.news_sources.map((src, i) => (
                <a
                  key={i}
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex items-start gap-2 rounded-md p-2 transition hover:bg-card"
                >
                  <ExternalLink className="mt-0.5 h-3 w-3 shrink-0 text-accent opacity-60 group-hover:opacity-100" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs leading-snug text-text-primary group-hover:text-accent">
                      {src.title}
                    </p>
                    <p className="mt-0.5 text-[10px] text-text-muted">
                      {src.source}
                      {src.published_at && (
                        <> &middot; {new Date(src.published_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</>
                      )}
                    </p>
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <p className="text-xs text-text-muted">
              Based on market data and technical analysis
            </p>
          )}
        </div>
      )}

      {/* Confidence bar */}
      <div className="mt-3">
        <div className="h-1.5 w-full rounded-full bg-elevated overflow-hidden">
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
            <span className="text-bullish">
              Target: +{suggestion.target_pct}%
            </span>
          )}
          {suggestion.stop_loss_pct != null && (
            <span className="text-bearish">
              SL: -{suggestion.stop_loss_pct}%
            </span>
          )}
        </div>
      )}

      {/* Sector badge + tags */}
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <span className="rounded bg-elevated px-2 py-0.5 text-[10px] text-text-secondary">
          {suggestion.sector}
        </span>
        {suggestion.tags?.map((tag) => (
          <span
            key={tag}
            className="rounded bg-accent/10 px-2 py-0.5 text-[10px] font-medium text-accent"
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
                <TrendingUp className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" />
                <p className="text-xs leading-relaxed text-text-secondary">
                  {suggestion.rationale}
                </p>
              </div>
              <div className="flex items-start gap-2">
                <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
                <p className="text-xs text-text-secondary">
                  <span className="font-medium text-text-primary">Catalyst:</span>{" "}
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
