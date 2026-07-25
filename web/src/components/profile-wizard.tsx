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
  /** large = centered landing form; compact = left rail after analyze */
  size?: "large" | "compact";
}

export function ProfileWizard({
  onSubmit,
  loading,
  size = "large",
}: Props) {
  const t = useTranslations("wizard");
  const locale = useLocale() as Locale;
  const large = size === "large";

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
    <div
      className={cn(
        "glass shadow-ambient-lg",
        large ? "rounded-2xl p-8 md:p-10" : "rounded-xl2 p-6",
      )}
    >
      <div
        className={cn(
          "mb-1 flex items-center gap-2 font-semibold text-on-surface",
          large ? "text-lg md:text-xl" : "text-sm",
        )}
      >
        <Sparkles
          className={cn(
            "text-secondary-container",
            large ? "h-5 w-5" : "h-4 w-4",
          )}
        />
        {t("heading")}
      </div>
      <p
        className={cn(
          "text-on-surface-variant",
          large ? "mb-8 text-sm md:text-base" : "mb-5 text-xs",
        )}
      >
        {t("subheading")}
      </p>

      <div className={cn("flex items-center gap-2", large ? "mb-8" : "mb-6")}>
        {steps.map((label, i) => (
          <div key={label} className="flex flex-1 flex-col gap-1.5">
            <div
              className={cn(
                "rounded-full transition-colors duration-300",
                large ? "h-1.5" : "h-1",
                i <= step ? "bg-primary-container" : "bg-outline-variant/40",
              )}
            />
            <span
              className={cn(
                "uppercase tracking-wide",
                large ? "text-xs" : "text-[10px]",
                i === step ? "text-primary-container" : "text-outline-variant",
              )}
            >
              {label}
            </span>
          </div>
        ))}
      </div>

      <div className={cn(large ? "min-h-[200px]" : "min-h-[150px]")}>
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.25 }}
            className={cn("space-y-4", large && "space-y-5")}
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

      <div
        className={cn(
          "flex items-center justify-between gap-3",
          large ? "mt-8" : "mt-6",
        )}
      >
        <Button
          variant="ghost"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0 || loading}
          className={cn(step === 0 && "invisible", large && "px-6 py-3 text-base")}
        >
          <ArrowLeft className="h-4 w-4" />
          {t("back")}
        </Button>

        {step < steps.length - 1 ? (
          <Button
            onClick={() => setStep((s) => s + 1)}
            className={cn(large && "px-6 py-3 text-base")}
          >
            {t("next")}
            <ArrowRight className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            onClick={submit}
            disabled={loading}
            className={cn(large && "px-6 py-3 text-base")}
          >
            {loading ? t("analyzing") : t("submit")}
            {!loading && <Sparkles className="h-4 w-4" />}
          </Button>
        )}
      </div>
    </div>
  );
}
