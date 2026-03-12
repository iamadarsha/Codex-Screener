"use client";

import { useMemo, useState } from "react";
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
import { useLivePrices } from "@/hooks/use-live-prices";

export default function WatchlistPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const { data: items, isLoading } = useWatchlist();
  const addMutation = useAddToWatchlist();
  const removeMutation = useRemoveFromWatchlist();

  const symbols = useMemo(
    () => (items ?? []).map((i) => i.symbol),
    [items]
  );

  const livePrices = useLivePrices(symbols);

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
        <div className="space-y-6">
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

          <WatchlistSummary prices={livePrices} count={items?.length ?? 0} />

          {isLoading ? (
            <SkeletonTable rows={5} />
          ) : (
            <div className="rounded-panel border border-border bg-card">
              <WatchlistTable
                items={enrichedItems}
                onRemove={(symbol) => removeMutation.mutate(symbol)}
              />
            </div>
          )}

          <AddStockModal
            open={modalOpen}
            onClose={() => setModalOpen(false)}
            onAdd={(symbol) => addMutation.mutate(symbol)}
            existingSymbols={symbols}
          />
        </div>
      </PageTransition>
    </AppShell>
  );
}
