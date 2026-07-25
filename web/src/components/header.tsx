"use client";

import { useTranslations } from "next-intl";
import { LanguageSwitcher } from "./language-switcher";

export function Header() {
  const t = useTranslations("app");

  return (
    <header className="fixed top-0 z-50 flex w-full items-center justify-between border-b border-white/20 bg-white/40 px-lg py-4 shadow-sm backdrop-blur-2xl transition-colors duration-300">
      <div className="flex items-center gap-4">
        <span className="text-headline-md font-bold tracking-tighter text-primary">
          {t("title")}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <LanguageSwitcher />
      </div>
    </header>
  );
}
