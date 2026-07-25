"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  Check,
  ExternalLink,
  FileText,
  Volume2,
} from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

import { EligibilityBadge } from "./eligibility-badge";
import { Locale, localeToSpeechLang } from "@/i18n/config";
import type { Scheme } from "@/lib/types";
import { useSpeechSynthesis } from "@/lib/use-speech";
import { cn } from "@/lib/utils";

export function SchemeCard({ scheme, index }: { scheme: Scheme; index: number }) {
  const t = useTranslations("results");
  const locale = useLocale() as Locale;
  const { speak, speaking, supported } = useSpeechSynthesis();

  const isNearMiss =
    (scheme.eligibility_status || "").toLowerCase().includes("near");
  const link = scheme.apply_url || scheme.source_url;
  const docs = scheme.documents_required ?? [];

  function readAloud() {
    const label = isNearMiss ? t("nearMiss") : t("eligible");
    speak(`${scheme.scheme_name}. ${label}. ${scheme.reason}`, localeToSpeechLang[locale]);
  }

  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06, ease: [0.4, 0, 0.2, 1] }}
      className={cn(
        "glass glass-hover accent-line flex h-full flex-col overflow-hidden p-5",
        isNearMiss && "border-amber-400/40",
      )}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <h3 className="text-[15px] font-bold leading-snug text-on-surface">
          {scheme.scheme_name}
        </h3>
        {isNearMiss ? (
          <span className="inline-flex flex-shrink-0 items-center gap-1.5 rounded-full border border-amber-400/40 bg-amber-50 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-amber-700">
            <AlertTriangle className="h-3 w-3" strokeWidth={3} />
            {t("nearMiss")}
          </span>
        ) : (
          <EligibilityBadge label={t("eligible")} />
        )}
      </div>

      <p className="flex-grow text-[13px] leading-relaxed text-on-surface-variant">
        {scheme.reason}
      </p>

      {docs.length > 0 && (
        <div className="mt-4 rounded-lg border border-[#E0E0E0] bg-surface-container-low/60 p-3">
          <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-on-surface-variant">
            {t("documents")}
          </div>
          <ul className="space-y-1.5">
            {docs.map((doc, i) => (
              <li key={i} className="flex items-start gap-2 text-[12px] text-on-surface">
                <Check className="mt-0.5 h-3 w-3 flex-shrink-0 text-secondary-container" strokeWidth={3} />
                {doc}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-[#E0E0E0] pt-3">
        {!isNearMiss && link && (
          <a
            href={link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary-container transition-colors hover:text-secondary"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            {t("apply")}
          </a>
        )}
        {supported && (
          <button
            type="button"
            onClick={readAloud}
            aria-label={t("listen")}
            className={cn(
              "inline-flex items-center gap-1.5 text-xs font-medium text-on-surface-variant transition-colors hover:text-primary",
              speaking && "text-secondary-container",
            )}
          >
            <Volume2 className="h-3.5 w-3.5" />
            {t("listen")}
          </button>
        )}
        {scheme.source && (
          <span className="inline-flex items-center gap-1.5 text-[11px] text-outline-variant">
            <FileText className="h-3.5 w-3.5" />
            {scheme.source}
          </span>
        )}
      </div>
    </motion.article>
  );
}
