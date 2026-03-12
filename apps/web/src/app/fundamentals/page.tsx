import { AppShell } from "@/components/layout/app-shell";
import { Card } from "@/components/ui/card";

export default function FundamentalsPage() {
  return (
    <AppShell>
      <Card>
        <div className="text-xs uppercase tracking-[0.22em] text-[#5C5D6E]">
          Fundamentals
        </div>
        <h1 className="mt-2 text-3xl font-bold text-white">
          Quality and valuation filters
        </h1>
        <p className="mt-3 text-sm text-[#9899A8]">
          Range filters, quality scoring, and expanded analytics are staged for
          the frontend build phase.
        </p>
      </Card>
    </AppShell>
  );
}

