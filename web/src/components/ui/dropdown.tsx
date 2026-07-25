"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

type Option = { value: string; label: string };

interface DropdownProps {
  id?: string;
  value: string;
  options: Array<string | Option>;
  onChange: (value: string) => void;
  placeholder?: string;
  /** Optional leading icon shown inside the trigger. */
  icon?: React.ReactNode;
  /** Smaller trigger sized to content — used in the header. */
  compact?: boolean;
  disabled?: boolean;
  ariaLabel?: string;
  className?: string;
}

function normalize(opt: string | Option): Option {
  return typeof opt === "string" ? { value: opt, label: opt } : opt;
}

/**
 * Themed, animated single-select. Replaces the native <select> so the option
 * list can animate open/closed with a staggered reveal and a rotating chevron.
 * Closes on outside-click or Escape. Accepts plain string options or
 * {value,label} pairs.
 */
export function Dropdown({
  id,
  value,
  options,
  onChange,
  placeholder = "Select…",
  icon,
  compact = false,
  disabled = false,
  ariaLabel,
  className,
}: DropdownProps) {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);
  const activeRef = React.useRef<HTMLLIElement>(null);

  const items = React.useMemo(() => options.map(normalize), [options]);
  const selected = items.find((o) => o.value === value);

  React.useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  React.useEffect(() => {
    if (open) activeRef.current?.scrollIntoView({ block: "nearest" });
  }, [open]);

  return (
    <div
      ref={ref}
      className={cn("relative", compact ? "inline-block" : "w-full", className)}
    >
      <button
        id={id}
        type="button"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        data-open={open}
        className={cn(
          "flex items-center justify-between gap-2 rounded-lg border border-[#E0E0E0] bg-white text-on-surface transition-all hover:border-secondary-container/60 focus:outline-none focus:ring-2 focus:ring-secondary-container/20 data-[open=true]:border-secondary-container disabled:opacity-50",
          compact ? "h-9 w-full px-3 text-xs" : "h-11 w-full px-4 text-sm",
        )}
      >
        <span className="flex min-w-0 items-center gap-2">
          {icon && <span className="flex-shrink-0 text-on-surface-variant">{icon}</span>}
          <span className={cn("truncate", !selected && "text-outline-variant")}>
            {selected ? selected.label : placeholder}
          </span>
        </span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="flex-shrink-0"
        >
          <ChevronDown className="h-4 w-4 text-on-surface-variant" />
        </motion.span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.ul
            role="listbox"
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.16, ease: [0.4, 0, 0.2, 1] }}
            className={cn(
              "absolute right-0 z-50 mt-2 max-h-60 w-full overflow-auto rounded-lg border border-[#E0E0E0] bg-white p-1 shadow-ambient",
              compact && "min-w-[9rem]",
            )}
          >
            {items.map((opt, i) => {
              const active = opt.value === value;
              return (
                <motion.li
                  key={opt.value}
                  ref={active ? activeRef : undefined}
                  role="option"
                  aria-selected={active}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: Math.min(i * 0.018, 0.25) }}
                  onClick={() => {
                    onChange(opt.value);
                    setOpen(false);
                  }}
                  className={cn(
                    "flex cursor-pointer items-center justify-between gap-2 rounded-md px-3 py-2 text-on-surface-variant transition-colors hover:bg-surface-container-low hover:text-on-surface",
                    compact ? "text-xs" : "text-sm",
                    active && "bg-secondary-container/10 text-primary-container",
                  )}
                >
                  <span className="truncate">{opt.label}</span>
                  {active && (
                    <Check className="h-3.5 w-3.5 flex-shrink-0 text-secondary-container" />
                  )}
                </motion.li>
              );
            })}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
