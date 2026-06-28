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
        isNearMiss && "border-amber-400/20",
      )}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <h3 className="text-[15px] font-bold leading-snug text-white">
          {scheme.scheme_name}
        </h3>
        {isNearMiss ? (
          <span className="inline-flex flex-shrink-0 items-center gap-1.5 rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-amber-300">
            <AlertTriangle className="h-3 w-3" strokeWidth={3} />
            {t("nearMiss")}
          </span>
        ) : (
          <EligibilityBadge label={t("eligible")} />
        )}
      </div>

      <p className="flex-grow text-[13px] leading-relaxed text-white/55">
        {scheme.reason}
      </p>

      {/* Document checklist (actionability) */}
      {docs.length > 0 && (
        <div className="mt-4 rounded-xl border border-white/5 bg-white/[0.02] p-3">
          <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-white/40">
            {t("documents")}
          </div>
          <ul className="space-y-1.5">
            {docs.map((doc, i) => (
              <li key={i} className="flex items-start gap-2 text-[12px] text-white/65">
                <Check className="mt-0.5 h-3 w-3 flex-shrink-0 text-emerald-400" strokeWidth={3} />
                {doc}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-white/5 pt-3">
        {!isNearMiss && link && (
          <a
            href={link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-300 transition-colors hover:text-emerald-200"
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
              "inline-flex items-center gap-1.5 text-xs font-medium text-white/50 transition-colors hover:text-white",
              speaking && "text-violet-300",
            )}
          >
            <Volume2 className="h-3.5 w-3.5" />
            {t("listen")}
          </button>
        )}
        {scheme.source && (
          <span className="inline-flex items-center gap-1.5 text-[11px] text-white/35">
            <FileText className="h-3.5 w-3.5" />
            {scheme.source}
          </span>
        )}
      </div>
    </motion.article>
  );
}
