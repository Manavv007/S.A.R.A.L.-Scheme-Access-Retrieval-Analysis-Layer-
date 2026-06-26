import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "h-11 w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 text-sm text-white placeholder:text-white/30 transition-all focus:border-emerald-400/60 focus:outline-none focus:ring-2 focus:ring-emerald-400/15",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";
