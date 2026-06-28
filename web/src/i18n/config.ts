export const locales = ["en", "hi", "gu", "te", "mr", "ta"] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "en";

export const localeNames: Record<Locale, string> = {
  en: "English",
  hi: "हिन्दी",
  gu: "ગુજરાતી",
  te: "తెలుగు",
  mr: "मराठी",
  ta: "தமிழ்",
};

// Maps a UI locale to the language name the backend expects for responses.
export const localeToBackendLanguage: Record<Locale, string> = {
  en: "English",
  hi: "Hindi",
  gu: "Gujarati",
  te: "Telugu",
  mr: "Marathi",
  ta: "Tamil",
};

// BCP-47 language tags for the Web Speech APIs (STT + TTS).
export const localeToSpeechLang: Record<Locale, string> = {
  en: "en-IN",
  hi: "hi-IN",
  gu: "gu-IN",
  te: "te-IN",
  mr: "mr-IN",
  ta: "ta-IN",
};

export const LOCALE_COOKIE = "SARAL_LOCALE";
