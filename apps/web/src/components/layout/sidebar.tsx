"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BellRing,
  ChartCandlestick,
  LayoutDashboard,
  SearchCheck,
  Target,
  WalletCards,
} from "lucide-react";

const navigationItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/screener", label: "Screener", icon: SearchCheck },
  { href: "/chart/RELIANCE", label: "Chart", icon: ChartCandlestick },
  { href: "/watchlist", label: "Watchlist", icon: WalletCards },
  { href: "/fundamentals", label: "Fundamentals", icon: Target },
  { href: "/alerts", label: "Alerts", icon: BellRing },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-[220px] flex-col border-r border-[#191a22] bg-sidebar px-4 py-5 lg:flex">
      <Link href="/" className="mb-8 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#7C5CFC] to-[#5B3FD4] font-semibold text-white shadow-accent">
          B
        </div>
        <div>
          <div className="text-sm font-semibold text-white">BreakoutScan</div>
          <div className="text-xs uppercase tracking-[0.2em] text-[#5C5D6E]">
            Live terminal
          </div>
        </div>
      </Link>

      <nav className="space-y-2">
        {navigationItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname.startsWith(href);

          return (
            <Link
              key={href}
              href={href}
              className={`relative flex items-center gap-3 rounded-lg px-4 py-3 text-sm transition ${
                isActive
                  ? "bg-[rgba(124,92,252,0.2)] text-white"
                  : "text-[#9899A8] hover:bg-[#171922] hover:text-white"
              }`}
            >
              {isActive ? (
                <span className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-accent" />
              ) : null}
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

