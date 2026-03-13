import { cn } from "@/lib/cn";
import type { ReactNode } from "react";

type BadgeVariant = "bullish" | "bearish" | "neutral" | "accent" | "warning";

interface BadgeProps {
  variant?: BadgeVariant;
  children: ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  bullish:
    "bg-bullish/[0.12] text-bullish border-bullish/25",
  bearish:
    "bg-bearish/[0.12] text-bearish border-bearish/25",
  neutral:
    "bg-text-secondary/[0.12] text-text-secondary border-text-secondary/25",
  accent:
    "bg-accent/[0.12] text-accent-hover border-accent/25",
  warning:
    "bg-warning/[0.12] text-warning border-warning/25",
};

export function Badge({ variant = "neutral", children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
