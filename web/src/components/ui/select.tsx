import * as React from "react";

import { cn } from "@/lib/utils";

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: string[];
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, options, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "h-11 w-full appearance-none rounded-xl border border-white/10 bg-white/[0.03] px-4 text-sm text-white transition-all focus:border-emerald-400/60 focus:outline-none focus:ring-2 focus:ring-emerald-400/15",
        className,
      )}
      {...props}
    >
      {options.map((opt) => (
        <option key={opt} value={opt} className="bg-ink-800 text-white">
          {opt}
        </option>
      ))}
    </select>
  ),
);
Select.displayName = "Select";
