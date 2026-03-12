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
            className="text-xs font-medium uppercase tracking-wider text-[#8B8D9A]"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={cn(
            "h-10 rounded-lg border border-[#2A2B35] bg-[#13141A] px-3 text-sm text-[#E8E9F0] placeholder-[#5C5D6E] outline-none transition",
            "focus:border-[#7C5CFC] focus:ring-1 focus:ring-[rgba(124,92,252,0.3)]",
            "hover:border-[#3A3B45]",
            error && "border-[#FF4757] focus:border-[#FF4757] focus:ring-[rgba(255,71,87,0.3)]",
            className
          )}
          {...props}
        />
        {error && (
          <span className="text-xs text-[#FF4757]">{error}</span>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
