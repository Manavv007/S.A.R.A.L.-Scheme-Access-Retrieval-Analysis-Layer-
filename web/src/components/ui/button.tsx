import * as React from "react";

import { cn } from "@/lib/utils";

type Variant = "primary" | "ghost" | "outline";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-primary-container text-on-primary font-semibold shadow-ambient hover:bg-secondary hover:-translate-y-0.5",
  outline:
    "border border-outline-variant/40 bg-white text-primary hover:border-secondary-container hover:bg-surface-container-low",
  ghost: "text-on-surface-variant hover:text-primary hover:bg-surface-container-low",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary-container/40 disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
