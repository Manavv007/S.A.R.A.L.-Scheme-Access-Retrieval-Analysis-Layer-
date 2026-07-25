import type { Profile } from "@/lib/types";

/**
 * Map the eligibility-form Profile into the voice ConversationEngine slot shape.
 * Empty / null form → {} so the officer keeps the normal collect-from-age flow.
 */
export function formProfileToVoiceSlots(
  profile: Profile | null | undefined,
): Record<string, unknown> {
  if (!profile) return {};

  const slots: Record<string, unknown> = {};
  if (profile.age != null && profile.age !== ("" as unknown)) {
    slots.age = profile.age;
  }
  if (profile.occupation) slots.occupation = profile.occupation;
  if (profile.state) slots.state = profile.state;
  if (profile.income !== undefined && profile.income !== null && String(profile.income).trim() !== "") {
    // Engine accepts numeric income; strip non-digits when possible.
    const digits = String(profile.income).replace(/[^0-9]/g, "");
    slots.income = digits ? Number(digits) : profile.income;
  }
  if (profile.caste) slots.caste = profile.caste;
  return slots;
}

/** Short label for chat UI when a form profile is active. */
export function profileSummary(profile: Profile | null | undefined): string | null {
  if (!profile) return null;
  const incomeDigits = String(profile.income ?? "").replace(/[^0-9]/g, "");
  const incomeLabel = incomeDigits
    ? `Income ₹${Number(incomeDigits).toLocaleString("en-IN")}`
    : null;
  const parts = [
    profile.occupation,
    profile.state,
    profile.age != null ? `Age ${profile.age}` : null,
    incomeLabel,
    profile.caste || null,
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : null;
}
