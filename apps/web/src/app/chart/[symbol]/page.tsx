import { AppShell } from "@/components/layout/app-shell";
import { Card } from "@/components/ui/card";

type ChartPageProps = {
  params: Promise<{
    symbol: string;
  }>;
};

export default async function ChartPage({ params }: ChartPageProps) {
  const { symbol } = await params;

  return (
    <AppShell>
      <Card>
        <div className="text-xs uppercase tracking-[0.22em] text-[#5C5D6E]">
          Chart
        </div>
        <h1 className="mt-2 text-3xl font-bold text-white">{symbol}</h1>
        <p className="mt-3 text-sm text-[#9899A8]">
          Live charting, overlays, and indicator panes land in the chart phase.
        </p>
      </Card>
    </AppShell>
  );
}
