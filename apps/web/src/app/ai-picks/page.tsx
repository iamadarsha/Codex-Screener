"use client";

import { AppShell } from "@/components/layout/app-shell";
import { PageTransition } from "@/components/layout/page-transition";
import { SectionHeading } from "@/components/ui/section-heading";
import { SkeletonCard } from "@/components/ui/skeleton";
import { StockCard } from "@/components/ai-picks/stock-card";
import {
  useAiSuggestions,
  useRefreshAiSuggestions,
} from "@/hooks/use-ai-suggestions";
import { RefreshCw, Sparkles, Clock } from "lucide-react";
import { cn } from "@/lib/cn";

export default function AiPicksPage() {
  const { data, isLoading } = useAiSuggestions();
  const refresh = useRefreshAiSuggestions();

  const suggestions = data?.suggestions ?? [];
  const generatedAt = data?.generated_at
    ? new Date(data.generated_at).toLocaleString("en-IN", {
        timeZone: "Asia/Kolkata",
        dateStyle: "medium",
        timeStyle: "short",
      })
    : null;

  return (
    <AppShell>
      <PageTransition>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between">
            <SectionHeading
              title="AI Picks"
              subtitle="AI-powered stock suggestions based on latest market news"
            />
            <button
              onClick={() => refresh.mutate()}
              disabled={refresh.isPending}
              className={cn(
                "flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-[#8b95a8] transition hover:border-[#7c5cfc]/30 hover:text-white",
                refresh.isPending && "cursor-not-allowed opacity-50"
              )}
            >
              <RefreshCw
                className={cn(
                  "h-4 w-4",
                  refresh.isPending && "animate-spin"
                )}
              />
              {refresh.isPending ? "Generating..." : "Refresh"}
            </button>
          </div>

          {/* Meta info */}
          {generatedAt && (
            <div className="flex flex-wrap items-center gap-4 text-xs text-[#5a6478]">
              <span className="flex items-center gap-1">
                <Sparkles className="h-3 w-3" /> Powered by Gemini 2.5 Flash
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" /> Generated {generatedAt}
              </span>
              {data?.headline_count ? (
                <span>Based on {data.headline_count} news headlines</span>
              ) : null}
            </div>
          )}

          {/* Cards grid */}
          {isLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : suggestions.length === 0 ? (
            <div className="rounded-panel border border-border bg-card p-10 text-center">
              <Sparkles className="mx-auto h-8 w-8 text-[#5a6478]" />
              <p className="mt-3 text-sm text-[#8b95a8]">
                No AI suggestions available yet. Click Refresh to generate
                picks based on the latest market news.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {suggestions.map((s, i) => (
                <StockCard key={s.symbol} suggestion={s} index={i} />
              ))}
            </div>
          )}

          {/* Disclaimer */}
          <div className="rounded-panel border border-border bg-card/60 px-5 py-4">
            <p className="text-[11px] leading-relaxed text-[#5a6478]">
              Disclaimer: AI-generated suggestions are for informational
              purposes only and do not constitute financial advice. Always do
              your own research before making investment decisions. Past
              performance does not guarantee future results.
            </p>
          </div>
        </div>
      </PageTransition>
    </AppShell>
  );
}
