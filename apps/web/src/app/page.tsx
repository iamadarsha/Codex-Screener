"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Zap,
  ScanSearch,
  SlidersHorizontal,
  LineChart,
  Bell,
  BarChart3,
  ArrowRight,
  Gauge,
  Sparkles,
} from "lucide-react";

const features = [
  {
    icon: Zap,
    title: "Real-Time Scanning",
    description: "Live price feeds with sub-second latency. Breakout signals fire the moment conditions are met.",
    color: "text-[#00c796]",
    bg: "bg-[rgba(0,199,150,0.1)]",
    border: "border-[rgba(0,199,150,0.2)]",
  },
  {
    icon: ScanSearch,
    title: "12 Prebuilt Scans",
    description: "Volume breakouts, EMA crossovers, RSI divergence, MACD signals, and more ready to run.",
    color: "text-[#7c5cfc]",
    bg: "bg-[rgba(124,92,252,0.1)]",
    border: "border-[rgba(124,92,252,0.2)]",
  },
  {
    icon: SlidersHorizontal,
    title: "Custom Scanner",
    description: "Build your own scan conditions combining any indicator, timeframe, and universe filter.",
    color: "text-[#00d4ff]",
    bg: "bg-[rgba(0,212,255,0.1)]",
    border: "border-[rgba(0,212,255,0.2)]",
  },
  {
    icon: LineChart,
    title: "Technical Charts",
    description: "Interactive candlestick charts with overlays for EMA, Bollinger Bands, RSI, MACD, and volume.",
    color: "text-[#ff8800]",
    bg: "bg-[rgba(255,136,0,0.1)]",
    border: "border-[rgba(255,136,0,0.2)]",
  },
  {
    icon: Bell,
    title: "Smart Alerts",
    description: "Set price, volume, or indicator alerts. Get notified the instant your conditions trigger.",
    color: "text-[#ff5a8a]",
    bg: "bg-[rgba(255,90,138,0.1)]",
    border: "border-[rgba(255,90,138,0.2)]",
  },
  {
    icon: BarChart3,
    title: "Fundamentals",
    description: "Screen stocks by PE, PB, ROE, market cap, dividend yield, and debt-to-equity ratios.",
    color: "text-[#00c796]",
    bg: "bg-[rgba(0,199,150,0.1)]",
    border: "border-[rgba(0,199,150,0.2)]",
  },
];

const stats = [
  { label: "Stocks", value: "2000+", icon: BarChart3 },
  { label: "Scans", value: "12", icon: ScanSearch },
  { label: "Speed", value: "<1.5s", icon: Gauge },
  { label: "Free", value: "100%", icon: Sparkles },
];

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: "easeOut" as const },
  }),
};

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[var(--bg-page)]">
      {/* Hero */}
      <section className="relative flex flex-col items-center justify-center overflow-hidden px-6 pb-20 pt-32">
        {/* Glow orbs */}
        <div className="pointer-events-none absolute left-1/2 top-0 -translate-x-1/2">
          <div className="h-[600px] w-[800px] rounded-full bg-[radial-gradient(ellipse,rgba(124,92,252,0.15),transparent_70%)]" />
        </div>
        <div className="pointer-events-none absolute right-0 top-40">
          <div className="h-[400px] w-[400px] rounded-full bg-[radial-gradient(ellipse,rgba(0,212,255,0.08),transparent_70%)]" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative z-10 flex flex-col items-center text-center"
        >
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#7c5cfc] to-[#5b3fd4] text-xl font-bold text-white shadow-accent">
            B
          </div>
          <h1 className="mb-4 text-5xl font-bold tracking-tight text-white sm:text-6xl lg:text-7xl">
            <span className="gradient-text">BreakoutScan</span>
          </h1>
          <p className="mb-8 max-w-xl text-lg text-[#8b95a8] sm:text-xl">
            India&#39;s Real-Time Stock Breakout Scanner.
            <br className="hidden sm:block" />
            Spot momentum before the crowd.
          </p>
          <Link
            href="/dashboard"
            className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#7c5cfc] to-[#5b3fd4] px-8 py-3.5 text-sm font-semibold text-white shadow-accent transition hover:shadow-lg hover:brightness-110"
          >
            Open Dashboard
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </motion.div>
      </section>

      {/* Stats row */}
      <section className="relative z-10 mx-auto -mt-2 mb-20 max-w-3xl px-6">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              variants={fadeUp}
              className="flex flex-col items-center rounded-xl border border-[#232d40] bg-[#161d2d]/60 px-4 py-5 backdrop-blur"
            >
              <stat.icon className="mb-2 h-5 w-5 text-[#7c5cfc]" />
              <span className="text-2xl font-bold text-white">{stat.value}</span>
              <span className="mt-1 text-xs text-[#8b95a8]">{stat.label}</span>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Feature cards */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pb-32">
        <motion.h2
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-12 text-center text-2xl font-semibold text-white sm:text-3xl"
        >
          Everything you need to find breakouts
        </motion.h2>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feat, i) => (
            <motion.div
              key={feat.title}
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              variants={fadeUp}
              className={`group rounded-xl border ${feat.border} ${feat.bg} p-6 transition hover:border-opacity-60 hover:shadow-lg`}
            >
              <div className={`mb-4 inline-flex rounded-lg bg-[#1c2333] p-2.5 ${feat.color}`}>
                <feat.icon className="h-5 w-5" />
              </div>
              <h3 className="mb-2 text-base font-semibold text-white">{feat.title}</h3>
              <p className="text-sm leading-relaxed text-[#8b95a8]">{feat.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#232d40] px-6 py-8 text-center text-xs text-[#5a6478]">
        BreakoutScan &mdash; Built for Indian markets. Not financial advice.
      </footer>
    </div>
  );
}
