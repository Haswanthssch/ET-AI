import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Per-role accent palettes (README-inspired)
        executive: { DEFAULT: "#9f1239", light: "#e11d48", soft: "#4c0519" },
        procurement: { DEFAULT: "#b45309", light: "#f59e0b", soft: "#451a03" },
        engineer: { DEFAULT: "#b87333", light: "#ea9d5a", soft: "#3a2412" },
        qa: { DEFAULT: "#0f766e", light: "#14b8a6", soft: "#042f2e" },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "monospace"],
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseglow: {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out both",
        pulseglow: "pulseglow 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
