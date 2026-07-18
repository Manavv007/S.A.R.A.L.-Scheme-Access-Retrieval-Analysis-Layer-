"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

interface DropdownProps {
  id?: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
  placeholder?: string;
}

/**
 * Themed, animated single-select. Replaces the native <select> so the option
 * list can animate open/closed with a staggered reveal and a rotating chevron.
 * Closes on outside-click or Escape.
 */
export function Dropdown({
  id,
  value,
  options,
  onChange,
  placeholder = "Select…",
}: DropdownProps) {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);
  const activeRef = React.useRef<HTMLLIElement>(null);

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
    <div ref={ref} className="relative">
      <button
        id={id}
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        data-open={open}
        className="flex h-11 w-full items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 text-sm text-white transition-all hover:border-emerald-400/40 focus:outline-none focus:ring-2 focus:ring-emerald-400/15 data-[open=true]:border-emerald-400/60"
      >
        <span className={cn("truncate", !value && "text-white/30")}>
          {value || placeholder}
        </span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="flex-shrink-0"
        >
          <ChevronDown className="h-4 w-4 text-white/50" />
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
            className="absolute z-50 mt-2 max-h-60 w-full overflow-auto rounded-xl border border-white/10 bg-ink-800/95 p-1 shadow-[0_20px_50px_-20px_rgba(0,0,0,0.8)] backdrop-blur-xl"
          >
            {options.map((opt, i) => {
              const active = opt === value;
              return (
                <motion.li
                  key={opt}
                  ref={active ? activeRef : undefined}
                  role="option"
                  aria-selected={active}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: Math.min(i * 0.018, 0.25) }}
                  onClick={() => {
                    onChange(opt);
                    setOpen(false);
                  }}
                  className={cn(
                    "flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-sm text-white/80 transition-colors hover:bg-emerald-400/10 hover:text-white",
                    active && "bg-emerald-400/15 text-emerald-200",
                  )}
                >
                  <span className="truncate">{opt}</span>
                  {active && (
                    <Check className="h-3.5 w-3.5 flex-shrink-0 text-emerald-300" />
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
