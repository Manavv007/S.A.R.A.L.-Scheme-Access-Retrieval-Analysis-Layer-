import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#070708",
          900: "#0a0a0c",
          800: "#101014",
          700: "#16161c",
        },
        emerald: {
          glow: "#10b981",
        },
        violet: {
          glow: "#8b5cf6",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xl2: "1.25rem",
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
          "0%,100%": { boxShadow: "0 0 18px rgba(16,185,129,0.25)" },
          "50%": { boxShadow: "0 0 30px rgba(16,185,129,0.5)" },
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
