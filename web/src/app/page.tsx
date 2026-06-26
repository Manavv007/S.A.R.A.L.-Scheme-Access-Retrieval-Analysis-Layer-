"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChatPanel } from "@/components/chat-panel";
import { Header } from "@/components/header";
import { Metric } from "@/components/metric";
import { ProfileWizard } from "@/components/profile-wizard";
import { SchemeCard } from "@/components/scheme-card";
import { SkeletonCard } from "@/components/skeleton-card";
import type { Profile, Scheme } from "@/lib/types";

export default function HomePage() {
  const t = useTranslations("results");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [schemes, setSchemes] = useState<Scheme[] | null>(null);
  const [loading, setLoading] = useState(false);

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
      const recs: Scheme[] = (data.recommendations || []).filter(
        (s: Scheme) => (s.eligibility_status || "").toLowerCase() === "eligible",
      );
      setSchemes(recs);
    } catch {
      setSchemes([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-screen">
      <Header />

      <main className="mx-auto max-w-6xl px-5 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold tracking-tight gradient-text sm:text-4xl">
            {t("heading")}
          </h1>
        </div>

        <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
          {/* Left: wizard */}
          <div className="lg:sticky lg:top-24 lg:self-start">
            <ProfileWizard onSubmit={runCheck} loading={loading} />
          </div>

          {/* Right: results */}
          <section className="space-y-6">
            {profile && (
              <div className="grid grid-cols-3 gap-3">
                <Metric
                  label={t("found")}
                  value={loading ? "..." : schemes?.length ?? 0}
                />
                <Metric label={t("occupation")} value={profile.occupation} />
                <Metric label={t("state")} value={profile.state} />
              </div>
            )}

            {loading && (
              <div className="grid gap-4 sm:grid-cols-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <SkeletonCard key={i} />
                ))}
              </div>
            )}

            {!loading && schemes && schemes.length > 0 && (
              <div className="grid gap-4 sm:grid-cols-2">
                {schemes.map((s, i) => (
                  <SchemeCard key={`${s.scheme_name}-${i}`} scheme={s} index={i} />
                ))}
              </div>
            )}

            {!loading && schemes && schemes.length === 0 && (
              <div className="glass rounded-xl2 p-8 text-center text-sm text-white/50">
                {t("empty")}
              </div>
            )}

            {!profile && !loading && (
              <div className="glass rounded-xl2 p-8 text-center text-sm text-white/40">
                {t("empty")}
              </div>
            )}
          </section>
        </div>

        <div className="mt-8">
          <ChatPanel profile={profile} />
        </div>
      </main>
    </div>
  );
}
