"use client";

import { motion } from "framer-motion";
import { Minus, Plus } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

interface StepperProps {
  id?: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  /** Optional caption shown under the field (e.g. formatted currency). */
  caption?: string;
}

/**
 * Numeric input with animated increment / decrement buttons. The value is
 * still typeable in the centre; the +/- buttons spring on press and the
 * number gives a quick directional pop on each change.
 */
export function Stepper({
  id,
  value,
  onChange,
  min = 0,
  max = Number.MAX_SAFE_INTEGER,
  step = 1,
  caption,
}: StepperProps) {
  const [pop, setPop] = React.useState<0 | 1 | -1>(0);
  const clamp = (v: number) => Math.min(max, Math.max(min, v));

  const set = (next: number, dir: 1 | -1) => {
    const clamped = clamp(next);
    if (clamped === value) return;
    onChange(clamped);
    setPop(dir);
    window.setTimeout(() => setPop(0), 180);
  };

  const btn =
    "grid h-11 w-11 flex-shrink-0 place-items-center text-on-surface-variant transition-colors hover:text-primary disabled:cursor-not-allowed disabled:opacity-30";

  return (
    <div>
      <div className="flex h-11 items-center overflow-hidden rounded-lg border border-[#E0E0E0] bg-white transition-all focus-within:border-secondary-container focus-within:ring-2 focus-within:ring-secondary-container/20">
        <motion.button
          type="button"
          aria-label="Decrease"
          whileHover={{ scale: 1.12 }}
          whileTap={{ scale: 0.82 }}
          onClick={() => set(value - step, -1)}
          disabled={value <= min}
          className={cn(btn, "border-r border-[#E0E0E0]")}
        >
          <Minus className="h-4 w-4" />
        </motion.button>

        <motion.input
          id={id}
          type="number"
          inputMode="numeric"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(clamp(Number(e.target.value)))}
          animate={{
            scale: pop === 0 ? 1 : 1.14,
            y: pop === 0 ? 0 : pop === 1 ? -2 : 2,
            color: pop === 0 ? "#191c1d" : "#0d47a1",
          }}
          transition={{ type: "spring", stiffness: 500, damping: 18 }}
          className="h-full w-full [appearance:textfield] bg-transparent text-center text-sm font-semibold text-on-surface focus:outline-none [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
        />

        <motion.button
          type="button"
          aria-label="Increase"
          whileHover={{ scale: 1.12 }}
          whileTap={{ scale: 0.82 }}
          onClick={() => set(value + step, 1)}
          disabled={value >= max}
          className={cn(btn, "border-l border-[#E0E0E0]")}
        >
          <Plus className="h-4 w-4" />
        </motion.button>
      </div>

      {caption && (
        <p className="mt-1.5 text-center text-[11px] font-medium text-secondary-container">
          {caption}
        </p>
      )}
    </div>
  );
}
