"use client";

import type { ReactNode } from "react";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { IndexTickerBar } from "./index-ticker-bar";
import { MobileNav } from "./mobile-nav";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-page text-text-primary lg:flex">
      <Sidebar />
      <div className="flex min-h-screen flex-1 flex-col overflow-x-hidden min-w-0">
        <Topbar />
        <IndexTickerBar />
        <main className="flex-1 overflow-x-hidden px-3 py-4 pb-20 sm:p-6 lg:pb-6">{children}</main>
      </div>
      <MobileNav />
    </div>
  );
}
