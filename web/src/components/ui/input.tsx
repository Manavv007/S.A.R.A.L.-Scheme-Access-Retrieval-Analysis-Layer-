import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "h-11 w-full rounded-lg border border-[#E0E0E0] bg-white px-4 text-sm text-on-surface placeholder:text-outline-variant transition-all focus:border-secondary-container focus:outline-none focus:ring-2 focus:ring-secondary-container/20",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";
