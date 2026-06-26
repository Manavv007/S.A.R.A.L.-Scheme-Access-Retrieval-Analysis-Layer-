"use client";

import { motion } from "framer-motion";
import { ExternalLink, FileText } from "lucide-react";
import { useTranslations } from "next-intl";

import { EligibilityBadge } from "./eligibility-badge";
import type { Scheme } from "@/lib/types";

export function SchemeCard({ scheme, index }: { scheme: Scheme; index: number }) {
  const t = useTranslations("results");
  const link = scheme.apply_url || scheme.source_url;

  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06, ease: [0.4, 0, 0.2, 1] }}
      className="glass glass-hover accent-line flex h-full flex-col overflow-hidden p-5"
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <h3 className="text-[15px] font-bold leading-snug text-white">
          {scheme.scheme_name}
        </h3>
        <EligibilityBadge label={t("eligible")} />
      </div>

      <p className="flex-grow text-[13px] leading-relaxed text-white/55">
        {scheme.reason}
      </p>

      {(link || scheme.source) && (
        <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-white/5 pt-3">
          {link && (
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
          {scheme.source && (
            <span className="inline-flex items-center gap-1.5 text-[11px] text-white/35">
              <FileText className="h-3.5 w-3.5" />
              {scheme.source}
            </span>
          )}
        </div>
      )}
    </motion.article>
  );
}
