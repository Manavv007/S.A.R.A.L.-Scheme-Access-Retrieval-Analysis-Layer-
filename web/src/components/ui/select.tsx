import * as React from "react";

import { cn } from "@/lib/utils";

type SelectOption = string | { value: string; label: string };

export interface SelectProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "children"> {
  options: SelectOption[];
}

function optionValue(opt: SelectOption): string {
  return typeof opt === "string" ? opt : opt.value;
}

function optionLabel(opt: SelectOption): string {
  return typeof opt === "string" ? opt : opt.label;
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
      {options.map((opt) => {
        const value = optionValue(opt);
        return (
          <option key={value} value={value} className="bg-ink-800 text-white">
            {optionLabel(opt)}
          </option>
        );
      })}
    </select>
  ),
);
Select.displayName = "Select";
