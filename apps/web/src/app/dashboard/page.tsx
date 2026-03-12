import { AppShell } from "@/components/layout/app-shell";
import { Card } from "@/components/ui/card";

const statCards = [
  { label: "Breakout hits", value: "148", change: "+12.4%" },
  { label: "Active alerts", value: "64", change: "+4.1%" },
  { label: "Volume surges", value: "39", change: "+18.9%" },
  { label: "Breadth", value: "62%", change: "Bullish" },
] as const;

export default function DashboardPage() {
  return (
    <AppShell>
      <div className="grid gap-4 xl:grid-cols-4">
        {statCards.map((card) => (
          <Card key={card.label}>
            <div className="text-xs uppercase tracking-[0.22em] text-[#5C5D6E]">
              {card.label}
            </div>
            <div className="mt-4 flex items-end justify-between">
              <div className="font-mono text-3xl font-semibold text-white">
                {card.value}
              </div>
              <div className="text-sm text-[#00C896]">{card.change}</div>
            </div>
          </Card>
        ))}
      </div>
    </AppShell>
  );
}

