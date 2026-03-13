"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  SearchCheck,
  Sparkles,
  ChartCandlestick,
  Eye,
} from "lucide-react";
import { cn } from "@/lib/cn";

const items = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/screener", label: "Screener", icon: SearchCheck },
  { href: "/ai-picks", label: "AI Picks", icon: Sparkles },
  { href: "/chart/RELIANCE", label: "Charts", icon: ChartCandlestick },
  { href: "/watchlist", label: "Watchlist", icon: Eye },
] as const;

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-card/95 backdrop-blur-xl safe-area-bottom lg:hidden">
      <div className="flex items-center justify-around px-1 py-1.5">
        {items.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href.split("/").slice(0, 2).join("/") + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-col items-center gap-0.5 rounded-lg px-3 py-1.5 text-[10px] font-medium transition",
                isActive
                  ? "text-accent"
                  : "text-text-muted active:text-text-primary"
              )}
            >
              <Icon className={cn("h-5 w-5", isActive && "drop-shadow-[0_0_6px_rgba(124,92,252,0.5)]")} />
              <span>{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
