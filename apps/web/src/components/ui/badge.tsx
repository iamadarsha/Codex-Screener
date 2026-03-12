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
    "bg-[rgba(0,200,150,0.12)] text-[#00C896] border-[rgba(0,200,150,0.25)]",
  bearish:
    "bg-[rgba(255,71,87,0.12)] text-[#FF4757] border-[rgba(255,71,87,0.25)]",
  neutral:
    "bg-[rgba(139,141,154,0.12)] text-[#8B8D9A] border-[rgba(139,141,154,0.25)]",
  accent:
    "bg-[rgba(124,92,252,0.12)] text-[#9B7FFF] border-[rgba(124,92,252,0.25)]",
  warning:
    "bg-[rgba(255,165,2,0.12)] text-[#FFA502] border-[rgba(255,165,2,0.25)]",
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
