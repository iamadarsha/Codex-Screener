import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const metrics = [
  { label: "Live symbols", value: "2,000+" },
  { label: "Prebuilt scans", value: "12" },
  { label: "Realtime latency", value: "< 1s" },
] as const;

export default function LandingPage() {
  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-16">
      <div className="mb-10 max-w-3xl">
        <div className="mb-4 inline-flex rounded-full border border-[rgba(124,92,252,0.35)] bg-[rgba(124,92,252,0.12)] px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-[#9B7FFF]">
          Breakout terminal for Indian markets
        </div>
        <h1 className="mb-4 text-5xl font-extrabold leading-tight text-white">
          Scan NSE and BSE breakouts with a trading-desk interface.
        </h1>
        <p className="max-w-2xl text-lg text-[#9899A8]">
          BreakoutScan combines live market data, prebuilt setups, alerts, and
          chart-first workflows in a single dark terminal-inspired platform.
        </p>
      </div>

      <div className="mb-12 flex flex-wrap gap-4">
        <Link href="/dashboard">
          <Button>Open dashboard</Button>
        </Link>
        <Link href="/screener">
          <Button variant="secondary">Explore scans</Button>
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {metrics.map((metric) => (
          <Card key={metric.label}>
            <div className="text-xs uppercase tracking-[0.22em] text-[#5C5D6E]">
              {metric.label}
            </div>
            <div className="mt-3 font-mono text-3xl font-semibold text-white">
              {metric.value}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

