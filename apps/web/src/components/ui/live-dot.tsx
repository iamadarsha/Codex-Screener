import { cn } from "@/lib/cn";

interface LiveDotProps {
  className?: string;
  color?: "green" | "red" | "yellow";
}

const colorMap = {
  green: "bg-[#00C896]",
  red: "bg-[#FF4757]",
  yellow: "bg-[#FFA502]",
};

export function LiveDot({ className, color = "green" }: LiveDotProps) {
  return (
    <span className={cn("relative flex h-2.5 w-2.5", className)}>
      <span
        className={cn(
          "absolute inline-flex h-full w-full animate-ping rounded-full opacity-75",
          colorMap[color]
        )}
      />
      <span
        className={cn(
          "relative inline-flex h-2.5 w-2.5 rounded-full",
          colorMap[color]
        )}
      />
    </span>
  );
}
