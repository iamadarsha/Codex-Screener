import type { ReactNode } from "react";

type CardProps = {
  children: ReactNode;
  className?: string;
};

export function Card({ children, className = "" }: CardProps) {
  return (
    <div
      className={`rounded-panel border border-border bg-card p-5 shadow-card transition duration-200 hover:-translate-y-0.5 hover:border-[#20222d] ${className}`}
    >
      {children}
    </div>
  );
}

