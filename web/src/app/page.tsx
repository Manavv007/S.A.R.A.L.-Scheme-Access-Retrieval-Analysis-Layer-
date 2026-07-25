"use client";

import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChatConsultant } from "@/components/chat-consultant";
import { Footer } from "@/components/footer";
import { Header } from "@/components/header";
import { ProfileWizard } from "@/components/profile-wizard";
import { SchemeCard } from "@/components/scheme-card";
import { SkeletonCard } from "@/components/skeleton-card";
import type { Profile, Scheme } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function HomePage() {
  const t = useTranslations("results");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [schemes, setSchemes] = useState<Scheme[] | null>(null);
  const [loading, setLoading] = useState(false);
  const analyzed = profile !== null;

  async function runCheck(p: Profile) {
    setProfile(p);
    setLoading(true);
    setSchemes(null);
    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(p),
      });
      const data = await res.json();
      setSchemes((data.recommendations || []) as Scheme[]);
    } catch {
      setSchemes([]);
    } finally {
      setLoading(false);
    }
  }

  const eligible = (schemes ?? []).filter(
    (s) => !(s.eligibility_status || "").toLowerCase().includes("near"),
  );
  const nearMiss = (schemes ?? []).filter((s) =>
    (s.eligibility_status || "").toLowerCase().includes("near"),
  );

  return (
    <div className="relative z-0 flex min-h-screen flex-col">
      <Header />

      <main className="mx-auto flex w-full max-w-container-max flex-grow flex-col items-center px-margin-mobile pb-xxl pt-[88px] md:px-gutter">
        <section className="relative mb-xl mt-xl max-w-3xl text-center">
          <h1 className="mb-4 text-headline-xl-mobile font-bold text-primary-container md:text-headline-xl">
            Empowering Every Citizen
          </h1>
          <p className="mx-auto max-w-2xl text-body-lg text-on-surface-variant">
            Secure, transparent, and direct access to essential institutional
            services and eligibility frameworks.
          </p>
        </section>

        <section
          id="eligibility"
          className={cn(
            "flex w-full scroll-mt-28 items-start justify-center gap-8",
            analyzed ? "max-w-6xl flex-col lg:flex-row" : "max-w-2xl",
          )}
        >
          <motion.div
            layout
            transition={{ type: "spring", stiffness: 280, damping: 30 }}
            className={cn(
              "w-full shrink-0",
              analyzed ? "lg:sticky lg:top-28 lg:w-[400px]" : "w-full",
            )}
          >
            <ProfileWizard
              onSubmit={runCheck}
              loading={loading}
              size={analyzed ? "compact" : "large"}
            />
          </motion.div>

          <AnimatePresence>
            {analyzed && (
              <motion.section
                id="results"
                key="results"
                initial={{ opacity: 0, x: 48 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 48 }}
                transition={{ type: "spring", stiffness: 260, damping: 28, delay: 0.08 }}
                className="min-w-0 flex-1 space-y-6"
              >
                <h2 className="text-headline-lg text-primary-container">
                  {t("heading")}
                </h2>

                {loading && (
                  <div className="grid gap-4 sm:grid-cols-2">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <SkeletonCard key={i} />
                    ))}
                  </div>
                )}

                {!loading && eligible.length > 0 && (
                  <div className="grid gap-4 sm:grid-cols-2">
                    {eligible.map((s, i) => (
                      <SchemeCard
                        key={`${s.scheme_name}-${i}`}
                        scheme={s}
                        index={i}
                      />
                    ))}
                  </div>
                )}

                {!loading && schemes && eligible.length === 0 && (
                  <div className="glass rounded-xl p-8 text-center text-sm text-on-surface-variant">
                    {t("empty")}
                  </div>
                )}

                {!loading && nearMiss.length > 0 && (
                  <div className="space-y-4">
                    <div>
                      <h3 className="flex items-center gap-2 text-lg font-bold text-[#853100]">
                        <AlertTriangle className="h-4 w-4" />
                        {t("nearMissHeading")}
                      </h3>
                      <p className="mt-1 text-xs text-on-surface-variant">
                        {t("nearMissSub")}
                      </p>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      {nearMiss.map((s, i) => (
                        <SchemeCard
                          key={`nm-${s.scheme_name}-${i}`}
                          scheme={s}
                          index={i}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </motion.section>
            )}
          </AnimatePresence>
        </section>
      </main>

      <Footer />
      <ChatConsultant profile={profile} />
    </div>
  );
}
