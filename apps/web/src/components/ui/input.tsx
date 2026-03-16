import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-2">
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
            "h-11 rounded-xl border border-border bg-page px-4 text-sm text-text-primary placeholder-text-muted outline-none transition-all duration-200",
            "focus:border-accent focus:ring-2 focus:ring-accent/15",
            "hover:border-border",
            error && "border-bearish focus:border-bearish focus:ring-bearish/20",
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
