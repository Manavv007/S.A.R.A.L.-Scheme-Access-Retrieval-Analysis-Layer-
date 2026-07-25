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
        "h-11 w-full appearance-none rounded-lg border border-[#E0E0E0] bg-white px-4 text-sm text-on-surface transition-all focus:border-secondary-container focus:outline-none focus:ring-2 focus:ring-secondary-container/20",
        className,
      )}
      {...props}
    >
      {options.map((opt) => {
        const value = optionValue(opt);
        return (
          <option key={value} value={value} className="bg-white text-on-surface">
            {optionLabel(opt)}
          </option>
        );
      })}
    </select>
  ),
);
Select.displayName = "Select";
