import * as React from "react";

import { cn } from "@/lib/utils";

type Variant = "primary" | "ghost" | "outline";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-gradient-to-r from-emerald-500 to-emerald-400 text-ink-950 font-semibold shadow-[0_8px_30px_-8px_rgba(16,185,129,0.6)] hover:shadow-[0_12px_40px_-8px_rgba(16,185,129,0.8)] hover:-translate-y-0.5",
  outline:
    "border border-white/15 bg-white/[0.02] text-white hover:border-emerald-400/50 hover:bg-white/[0.05]",
  ghost: "text-white/70 hover:text-white hover:bg-white/[0.05]",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-sm transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40 disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
