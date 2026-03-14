"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
  BellRing,
  ChartCandlestick,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  SearchCheck,
  Sparkles,
  Target,
  Eye,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/cn";
import { useMarketStatus } from "@/hooks/use-market-breadth";

const mainNav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/screener", label: "Screener", icon: SearchCheck },
  { href: "/ai-picks", label: "AI Picks", icon: Sparkles },
  { href: "/chart/RELIANCE", label: "Charts", icon: ChartCandlestick },
  { href: "/watchlist", label: "Watchlist", icon: Eye },
] as const;

const analysisNav = [
  { href: "/fundamentals", label: "Fundamentals", icon: Target },
  { href: "/alerts", label: "Alerts", icon: BellRing },
] as const;

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const { data: status } = useMarketStatus();

  const isOpen = status?.is_open ?? false;

  const renderNavItem = ({
    href,
    label,
    icon: Icon,
  }: {
    href: string;
    label: string;
    icon: typeof LayoutDashboard;
  }) => {
    const isActive = pathname === href || pathname.startsWith(href + "/");

    return (
      <Link
        key={href}
        href={href}
        title={collapsed ? label : undefined}
        className={cn(
          "relative flex items-center rounded-lg py-2.5 text-sm font-medium transition",
          collapsed ? "justify-center px-2" : "gap-3 px-4",
          isActive
            ? "bg-accent/10 text-text-primary shadow-[inset_0_0_12px_rgba(124,92,252,0.08)]"
            : "text-text-secondary hover:bg-elevated hover:text-text-primary"
        )}
      >
        {isActive && (
          <span className="absolute inset-y-2 left-0 w-[3px] rounded-full bg-accent" />
        )}
        <Icon className="h-[18px] w-[18px] shrink-0" />
        {!collapsed && <span>{label}</span>}
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        "glass-sidebar hidden flex-col py-5 transition-all duration-300 lg:flex",
        collapsed ? "w-[68px] px-2" : "w-[230px] px-4"
      )}
    >
      {/* Logo */}
      <Link
        href="/"
        className={cn(
          "mb-6 flex items-center",
          collapsed ? "justify-center" : "gap-3"
        )}
      >
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-accent/70 text-base font-bold text-white shadow-accent">
          B
        </div>
        {!collapsed && (
          <div>
            <div className="text-sm font-semibold text-text-primary">BreakoutScan</div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-text-muted">
              Live terminal
            </div>
          </div>
        )}
      </Link>

      {/* Market status */}
      <div
        className={cn(
          "mb-5 flex items-center rounded-lg border border-border bg-page px-3 py-2",
          collapsed ? "justify-center" : "gap-2"
        )}
      >
        <span
          className={cn(
            "h-2 w-2 shrink-0 rounded-full pulse-dot",
            isOpen ? "bg-bullish" : "bg-bearish"
          )}
        />
        {!collapsed && (
          <span
            className={cn(
              "text-[10px] font-semibold uppercase tracking-[0.15em]",
              isOpen ? "text-bullish" : "text-bearish"
            )}
          >
            {isOpen ? "Market Open" : "Market Closed"}
          </span>
        )}
      </div>

      {/* Main nav */}
      {!collapsed && (
        <div className="mb-1 px-4 text-[10px] font-semibold uppercase tracking-[0.15em] text-text-muted">
          Main
        </div>
      )}
      <nav className="space-y-0.5">
        {mainNav.map((item) => renderNavItem(item))}
      </nav>

      {/* Analysis nav */}
      {!collapsed && (
        <div className="mb-1 mt-6 px-4 text-[10px] font-semibold uppercase tracking-[0.15em] text-text-muted">
          Analysis
        </div>
      )}
      {collapsed && <div className="my-3 border-t border-border" />}
      <nav className="space-y-0.5">
        {analysisNav.map((item) => renderNavItem(item))}
      </nav>

      <div className="flex-1" />

      {/* Bottom actions */}
      <div className="mt-4 space-y-1">
        <button
          onClick={() => router.push("/settings")}
          className={cn(
            "flex w-full items-center rounded-lg py-2.5 text-sm transition",
            collapsed ? "justify-center px-2" : "gap-3 px-4",
            pathname === "/settings"
              ? "bg-accent/10 text-text-primary"
              : "text-text-muted hover:bg-elevated hover:text-text-primary"
          )}
        >
          <Settings className="h-[18px] w-[18px] shrink-0" />
          {!collapsed && <span>Settings</span>}
        </button>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex w-full items-center justify-center rounded-lg py-2 text-text-muted transition hover:bg-elevated hover:text-text-primary"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
