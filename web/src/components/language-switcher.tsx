"use client";

import { Languages } from "lucide-react";
import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { useTransition } from "react";

import { setLocale } from "@/i18n/actions";
import { Locale, localeNames, locales } from "@/i18n/config";
import { cn } from "@/lib/utils";

export function LanguageSwitcher() {
  const locale = useLocale() as Locale;
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function onChange(next: Locale) {
    startTransition(async () => {
      await setLocale(next);
      router.refresh();
    });
  }

  return (
    <div className="flex items-center gap-2">
      <Languages className="h-4 w-4 text-white/40" />
      <select
        aria-label="Language"
        value={locale}
        disabled={isPending}
        onChange={(e) => onChange(e.target.value as Locale)}
        className={cn(
          "rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1.5 text-xs text-white/80 transition-colors focus:border-emerald-400/50 focus:outline-none",
          isPending && "opacity-50",
        )}
      >
        {locales.map((l) => (
          <option key={l} value={l} className="bg-ink-800">
            {localeNames[l]}
          </option>
        ))}
      </select>
    </div>
  );
}
