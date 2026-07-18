"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, ArrowRight, Sparkles } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useMemo, useState } from "react";

import { Button } from "./ui/button";
import { Dropdown } from "./ui/dropdown";
import { Label } from "./ui/label";
import { Stepper } from "./ui/stepper";
import { Locale, localeToBackendLanguage } from "@/i18n/config";
import { CATEGORIES, OCCUPATIONS, STATES } from "@/lib/constants";
import type { Profile } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  onSubmit: (profile: Profile) => void;
  loading: boolean;
}

export function ProfileWizard({ onSubmit, loading }: Props) {
  const t = useTranslations("wizard");
  const locale = useLocale() as Locale;

  const [step, setStep] = useState(0);
  const [age, setAge] = useState(25);
  const [state, setState] = useState(STATES[6]);
  const [occupation, setOccupation] = useState(OCCUPATIONS[0]);
  const [income, setIncome] = useState(100000);
  const [caste, setCaste] = useState(CATEGORIES[0]);

  const steps = useMemo(
    () => [t("stepProfile"), t("stepLocation"), t("stepFinance")],
    [t],
  );

  function submit() {
    onSubmit({
      age,
      state,
      occupation,
      income: String(income),
      caste,
      language: localeToBackendLanguage[locale],
    });
  }

  return (
    <div className="glass rounded-xl2 p-6">
      <div className="mb-1 flex items-center gap-2 text-sm font-semibold text-white">
        <Sparkles className="h-4 w-4 text-emerald-400" />
        {t("heading")}
      </div>
      <p className="mb-5 text-xs text-white/45">{t("subheading")}</p>

      {/* Step indicator */}
      <div className="mb-6 flex items-center gap-2">
        {steps.map((label, i) => (
          <div key={label} className="flex flex-1 flex-col gap-1.5">
            <div
              className={cn(
                "h-1 rounded-full transition-colors duration-300",
                i <= step ? "bg-emerald-400" : "bg-white/10",
              )}
            />
            <span
              className={cn(
                "text-[10px] uppercase tracking-wide",
                i === step ? "text-emerald-300" : "text-white/30",
              )}
            >
              {label}
            </span>
          </div>
        ))}
      </div>

      <div className="min-h-[150px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.25 }}
            className="space-y-4"
          >
            {step === 0 && (
              <>
                <div>
                  <Label htmlFor="age">{t("age")}</Label>
                  <Stepper
                    id="age"
                    min={1}
                    max={120}
                    value={age}
                    onChange={setAge}
                  />
                </div>
                <div>
                  <Label htmlFor="occupation">{t("occupation")}</Label>
                  <Dropdown
                    id="occupation"
                    options={OCCUPATIONS}
                    value={occupation}
                    onChange={setOccupation}
                  />
                </div>
              </>
            )}

            {step === 1 && (
              <div>
                <Label htmlFor="state">{t("state")}</Label>
                <Dropdown
                  id="state"
                  options={STATES}
                  value={state}
                  onChange={setState}
                />
              </div>
            )}

            {step === 2 && (
              <>
                <div>
                  <Label htmlFor="income">{t("income")}</Label>
                  <Stepper
                    id="income"
                    min={0}
                    step={10000}
                    value={income}
                    onChange={setIncome}
                    caption={new Intl.NumberFormat("en-IN", {
                      style: "currency",
                      currency: "INR",
                      maximumFractionDigits: 0,
                    }).format(income)}
                  />
                </div>
                <div>
                  <Label htmlFor="caste">{t("category")}</Label>
                  <Dropdown
                    id="caste"
                    options={CATEGORIES}
                    value={caste}
                    onChange={setCaste}
                  />
                </div>
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="mt-6 flex items-center justify-between gap-3">
        <Button
          variant="ghost"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0 || loading}
          className={cn(step === 0 && "invisible")}
        >
          <ArrowLeft className="h-4 w-4" />
          {t("back")}
        </Button>

        {step < steps.length - 1 ? (
          <Button onClick={() => setStep((s) => s + 1)}>
            {t("next")}
            <ArrowRight className="h-4 w-4" />
          </Button>
        ) : (
          <Button onClick={submit} disabled={loading}>
            {loading ? t("analyzing") : t("submit")}
            {!loading && <Sparkles className="h-4 w-4" />}
          </Button>
        )}
      </div>
    </div>
  );
}
