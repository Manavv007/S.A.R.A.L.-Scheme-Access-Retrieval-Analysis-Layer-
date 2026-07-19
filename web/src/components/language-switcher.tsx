"use client";

import { Languages } from "lucide-react";
import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { useTransition } from "react";

import { Dropdown } from "./ui/dropdown";
import { setLocale } from "@/i18n/actions";
import { Locale, localeNames, locales } from "@/i18n/config";

export function LanguageSwitcher() {
  const locale = useLocale() as Locale;
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function onChange(next: string) {
    startTransition(async () => {
      await setLocale(next as Locale);
      router.refresh();
    });
  }

  const options = locales.map((l) => ({ value: l, label: localeNames[l] }));

  return (
    <Dropdown
      value={locale}
      options={options}
      onChange={onChange}
      disabled={isPending}
      compact
      ariaLabel="Language"
      icon={<Languages className="h-4 w-4" />}
    />
  );
}
