import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const scans = [
  "Bullish Harami 15min",
  "Short Term Breakouts",
  "Potential Breakouts",
  "RSI Bounce",
  "EMA 9/21 Crossover",
  "MACD Bullish Cross",
] as const;

export default function ScreenerPage() {
  return (
    <AppShell>
      <div className="mb-6">
        <div className="text-xs uppercase tracking-[0.22em] text-[#5C5D6E]">
          Screener
        </div>
        <h1 className="mt-2 text-3xl font-bold text-white">Prebuilt scans</h1>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        {scans.map((scan) => (
          <Card key={scan} className="border-l-2 border-l-accent">
            <div className="text-sm font-semibold text-white">{scan}</div>
            <div className="mt-2 text-sm text-[#9899A8]">
              Phase 1 scaffold includes navigation, theming, and runtime wiring.
            </div>
            <Button className="mt-4 w-full">Run scan</Button>
          </Card>
        ))}
      </div>
    </AppShell>
  );
}

