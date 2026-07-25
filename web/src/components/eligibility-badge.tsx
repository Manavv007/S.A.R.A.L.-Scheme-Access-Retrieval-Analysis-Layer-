import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

export function EligibilityBadge({ label }: { label: string }) {
  return (
    <span
      className={cn(
        "inline-flex flex-shrink-0 items-center gap-1.5 rounded-full bg-primary-container px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-on-primary",
      )}
    >
      <Check className="h-3 w-3" strokeWidth={3} />
      {label}
    </span>
  );
}
