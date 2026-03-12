import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: ButtonVariant;
};

export function Button({
  children,
  className = "",
  variant = "primary",
  ...props
}: ButtonProps) {
  const variantClassName =
    variant === "primary"
      ? "bg-gradient-to-br from-[#7C5CFC] to-[#5B3FD4] text-white shadow-accent"
      : "border border-accent bg-transparent text-accent";

  return (
    <button
      className={`inline-flex h-10 items-center justify-center rounded-lg px-4 text-sm font-semibold transition duration-200 hover:opacity-90 ${variantClassName} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

