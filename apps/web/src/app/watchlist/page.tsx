"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageTransition } from "@/components/layout/page-transition";
import { SectionHeading } from "@/components/ui/section-heading";
import { Button } from "@/components/ui/button";
import { SkeletonTable } from "@/components/ui/skeleton";
import { WatchlistTable } from "@/components/watchlist/watchlist-table";
import { WatchlistSummary } from "@/components/watchlist/watchlist-summary";
import { AddStockModal } from "@/components/watchlist/add-stock-modal";
import {
  useWatchlist,
  useAddToWatchlist,
  useRemoveFromWatchlist,
} from "@/hooks/use-watchlist";
import { useQuery } from "@tanstack/react-query";
import { useLivePrices } from "@/hooks/use-live-prices";
import { fetchLivePrices } from "@/lib/api";
import type { LivePrice } from "@/lib/api-types";

export default function WatchlistPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const { data: items, isLoading, isError } = useWatchlist();
  const addMutation = useAddToWatchlist();
  const removeMutation = useRemoveFromWatchlist();

  const symbols = useMemo(
    () => (items ?? []).map((i) => i.symbol),
    [items]
  );

  const wsPrices = useLivePrices(symbols);
  const hasWsPrices = Object.keys(wsPrices).length > 0;

  // REST fallback for when WebSocket doesn't deliver (e.g. market closed)
  const { data: restPriceList } = useQuery({
    queryKey: ["batchPrices", symbols.join(",")],
    queryFn: () => fetchLivePrices(symbols),
    enabled: symbols.length > 0 && !hasWsPrices,
    retry: 0,
    staleTime: 30_000,
  });
  const restPrices = useMemo(() => {
    const map: Record<string, LivePrice> = {};
    for (const p of restPriceList ?? []) map[p.symbol] = p;
    return map;
  }, [restPriceList]);

  const livePrices = hasWsPrices ? wsPrices : restPrices;

  const enrichedItems = useMemo(
    () =>
      (items ?? []).map((item) => ({
        ...item,
        livePrice: livePrices[item.symbol],
      })),
    [items, livePrices]
  );

  return (
    <AppShell>
      <PageTransition>
        <motion.div
          className="space-y-6"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: {},
            visible: { transition: { staggerChildren: 0.08 } },
          }}
        >
          <motion.div
            variants={{
              hidden: { opacity: 0, y: 16 },
              visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" } },
            }}
          >
            <SectionHeading
              title="Watchlist"
              subtitle="Track your favourite stocks with live prices"
              action={
                <Button
                  onClick={() => setModalOpen(true)}
                  className="flex items-center gap-2"
                >
                  <Plus className="h-4 w-4" />
                  Add Stock
                </Button>
              }
            />
          </motion.div>

          <motion.div
            variants={{
              hidden: { opacity: 0, y: 16 },
              visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" } },
            }}
          >
            <WatchlistSummary prices={livePrices} count={items?.length ?? 0} />
          </motion.div>

          <motion.div
            variants={{
              hidden: { opacity: 0, y: 16 },
              visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" } },
            }}
          >
            {isLoading ? (
              <SkeletonTable rows={5} />
            ) : isError ? (
              <div className="rounded-panel border border-border bg-card p-8 text-center">
                <p className="text-sm text-text-muted">Unable to load watchlist. API may be offline.</p>
                <p className="mt-1 text-xs text-text-muted">Add stocks to get started once the server is available.</p>
              </div>
            ) : (
              <div className="rounded-panel border border-border bg-card">
                <WatchlistTable
                  items={enrichedItems}
                  onRemove={(symbol) => removeMutation.mutate(symbol)}
                />
              </div>
            )}
          </motion.div>

          <AddStockModal
            open={modalOpen}
            onClose={() => setModalOpen(false)}
            onAdd={(symbol) => addMutation.mutate(symbol)}
            existingSymbols={symbols}
          />
        </motion.div>
      </PageTransition>
    </AppShell>
  );
}
