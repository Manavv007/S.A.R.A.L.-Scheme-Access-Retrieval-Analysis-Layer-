"use client";

import { useTranslations } from "next-intl";

import { LanguageSwitcher } from "./language-switcher";

export function Header() {
  const t = useTranslations("app");

  return (
    <header className="sticky top-0 z-30 border-b border-white/5 bg-ink-950/60 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl border border-white/10 bg-gradient-to-br from-emerald-500/20 to-violet-500/20 text-sm font-bold tracking-tight text-white">
            SL
          </div>
          <div>
            <div className="text-lg font-extrabold leading-none tracking-tight gradient-text">
              {t("title")}
            </div>
            <div className="mt-1 text-[11px] font-medium text-white/40">
              {t("subtitle")}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 sm:flex">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            <span className="text-xs font-semibold text-emerald-300">
              {t("online")}
            </span>
          </div>
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
}
