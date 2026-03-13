import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={id}
            className="text-xs font-medium uppercase tracking-wider text-text-secondary"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={cn(
            "h-10 rounded-lg border border-border bg-page px-3 text-sm text-text-primary placeholder-text-muted outline-none transition",
            "focus:border-accent focus:ring-1 focus:ring-accent-glow",
            "hover:border-border",
            error && "border-bearish focus:border-bearish focus:ring-bearish/30",
            className
          )}
          {...props}
        />
        {error && (
          <span className="text-xs text-bearish">{error}</span>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
