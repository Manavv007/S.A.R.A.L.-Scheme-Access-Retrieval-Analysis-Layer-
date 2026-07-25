import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/app/**/*.{ts,tsx}", "./src/components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#f8f9fa",
        surface: "#f8f9fa",
        "surface-dim": "#d9dadb",
        "surface-bright": "#f8f9fa",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f3f4f5",
        "surface-container": "#edeeef",
        "surface-container-high": "#e7e8e9",
        "surface-container-highest": "#e1e3e4",
        "surface-variant": "#e1e3e4",
        "on-surface": "#191c1d",
        "on-surface-variant": "#434652",
        "on-background": "#191c1d",
        outline: "#737783",
        "outline-variant": "#c3c6d4",
        primary: "#003178",
        "on-primary": "#ffffff",
        "primary-container": "#0d47a1",
        "on-primary-container": "#a1bbff",
        "primary-fixed": "#d9e2ff",
        "primary-fixed-dim": "#b0c6ff",
        "on-primary-fixed": "#001945",
        "on-primary-fixed-variant": "#00429c",
        secondary: "#0058bb",
        "on-secondary": "#ffffff",
        "secondary-container": "#1471e6",
        "on-secondary-container": "#fefcff",
        "secondary-fixed": "#d8e2ff",
        "secondary-fixed-dim": "#adc7ff",
        "on-secondary-fixed": "#001a41",
        "on-secondary-fixed-variant": "#004493",
        "surface-tint": "#2b5bb5",
        error: "#ba1a1a",
        "error-container": "#ffdad6",
        "on-error": "#ffffff",
        "on-error-container": "#93000a",
        // Keep legacy tokens used by some components during migration
        ink: {
          950: "#070708",
          900: "#0a0a0c",
          800: "#101014",
          700: "#16161c",
        },
        emerald: { glow: "#0d47a1" },
        violet: { glow: "#1471e6" },
      },
      fontFamily: {
        sans: [
          "var(--font-hanken)",
          "Hanken Grotesk",
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
        ],
      },
      fontSize: {
        "headline-xl": [
          "40px",
          { lineHeight: "48px", letterSpacing: "-0.02em", fontWeight: "700" },
        ],
        "headline-xl-mobile": [
          "32px",
          { lineHeight: "38px", letterSpacing: "-0.01em", fontWeight: "700" },
        ],
        "headline-lg": [
          "28px",
          { lineHeight: "36px", letterSpacing: "-0.01em", fontWeight: "600" },
        ],
        "headline-md": ["22px", { lineHeight: "28px", fontWeight: "600" }],
        "body-lg": ["18px", { lineHeight: "28px", fontWeight: "400" }],
        "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "body-sm": ["14px", { lineHeight: "20px", fontWeight: "400" }],
        "label-md": [
          "14px",
          { lineHeight: "16px", letterSpacing: "0.05em", fontWeight: "600" },
        ],
        "label-sm": ["12px", { lineHeight: "14px", fontWeight: "500" }],
      },
      spacing: {
        xs: "4px",
        sm: "8px",
        md: "16px",
        lg: "24px",
        xl: "40px",
        xxl: "64px",
        gutter: "24px",
        "margin-mobile": "16px",
        "container-max": "1280px",
      },
      maxWidth: {
        "container-max": "1280px",
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        lg: "0.5rem",
        xl: "0.75rem",
        xl2: "1rem",
        full: "9999px",
      },
      boxShadow: {
        ambient: "0px 2px 8px rgba(0, 0, 0, 0.04)",
        "ambient-lg": "0px 8px 24px rgba(0, 0, 0, 0.08)",
        "ambient-xl": "0px 16px 48px rgba(0, 0, 0, 0.12)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "pulse-glow": {
          "0%,100%": { boxShadow: "0 0 18px rgba(13,71,161,0.2)" },
          "50%": { boxShadow: "0 0 30px rgba(20,113,230,0.35)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s cubic-bezier(0.4,0,0.2,1) both",
        shimmer: "shimmer 1.6s infinite",
        "pulse-glow": "pulse-glow 2.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
