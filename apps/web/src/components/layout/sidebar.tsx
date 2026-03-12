"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  BellRing,
  ChartCandlestick,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  SearchCheck,
  Target,
  WalletCards,
} from "lucide-react";
import { cn } from "@/lib/cn";

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
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "hidden flex-col border-r border-[#191a22] bg-sidebar py-5 transition-all duration-300 lg:flex",
        collapsed ? "w-[68px] px-2" : "w-[220px] px-4"
      )}
    >
      <Link
        href="/"
        className={cn("mb-8 flex items-center", collapsed ? "justify-center" : "gap-3")}
      >
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#7C5CFC] to-[#5B3FD4] font-semibold text-white shadow-accent">
          B
        </div>
        {!collapsed && (
          <div>
            <div className="text-sm font-semibold text-white">BreakoutScan</div>
            <div className="text-xs uppercase tracking-[0.2em] text-[#5C5D6E]">
              Live terminal
            </div>
          </div>
        )}
      </Link>

      <nav className="flex-1 space-y-1">
        {navigationItems.map(({ href, label, icon: Icon }) => {
          const isActive =
            pathname === href || pathname.startsWith(href + "/");

          return (
            <Link
              key={href}
              href={href}
              title={collapsed ? label : undefined}
              className={cn(
                "relative flex items-center rounded-lg py-2.5 text-sm transition",
                collapsed ? "justify-center px-2" : "gap-3 px-4",
                isActive
                  ? "bg-[rgba(124,92,252,0.15)] text-white"
                  : "text-[#9899A8] hover:bg-[#171922] hover:text-white"
              )}
            >
              {isActive && (
                <span className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-accent" />
              )}
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{label}</span>}
            </Link>
          );
        })}
      </nav>

      <button
        onClick={() => setCollapsed(!collapsed)}
        className="mt-4 flex items-center justify-center rounded-lg py-2 text-[#5C5D6E] transition hover:bg-[#171922] hover:text-white"
      >
        {collapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </button>
    </aside>
  );
}
