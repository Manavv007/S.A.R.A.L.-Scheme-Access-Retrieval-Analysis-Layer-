import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

export function EligibilityBadge({ label }: { label: string }) {
  return (
    <span
      className={cn(
        "inline-flex flex-shrink-0 items-center gap-1.5 rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-ink-950",
        "animate-pulse-glow",
      )}
    >
      <Check className="h-3 w-3" strokeWidth={3} />
      {label}
    </span>
  );
}
