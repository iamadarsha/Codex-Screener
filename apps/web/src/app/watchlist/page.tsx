import { AppShell } from "@/components/layout/app-shell";
import { Card } from "@/components/ui/card";

export default function WatchlistPage() {
  return (
    <AppShell>
      <Card>
        <div className="text-xs uppercase tracking-[0.22em] text-[#5C5D6E]">
          Watchlist
        </div>
        <h1 className="mt-2 text-3xl font-bold text-white">Tracked symbols</h1>
        <p className="mt-3 text-sm text-[#9899A8]">
          The table, row actions, and add-symbol modal arrive after the data API
          phase. The design system and shell are already active here.
        </p>
      </Card>
    </AppShell>
  );
}

