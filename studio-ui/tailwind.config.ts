import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#1111d4",
          50:  "#eeeeff",
          100: "#d4d4ff",
          200: "#ababff",
          300: "#7777ff",
          400: "#4444ff",
          500: "#1111d4",
          600: "#0d0dab",
          700: "#090982",
          800: "#060659",
          900: "#030330",
        },
        background: {
          light: "#f6f6f8",
          dark:  "#101022",
        },
        surface: {
          dark: "#16162a",
        },
      },
      fontFamily: {
        display: ["var(--font-inter)", "Inter", "sans-serif"],
      },
      borderRadius: {
        lg: "0.625rem",
        xl: "0.875rem",
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "gradient-x": "gradient-x 6s ease infinite",
        "float": "float 6s ease-in-out infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
        "shimmer": "shimmer 2s linear infinite",
      },
      keyframes: {
        "gradient-x": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%":       { backgroundPosition: "100% 50%" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%":      { transform: "translateY(-12px)" },
        },
        glow: {
          from: { boxShadow: "0 0 10px rgba(17,17,212,0.4)" },
          to:   { boxShadow: "0 0 30px rgba(17,17,212,0.8), 0 0 60px rgba(17,17,212,0.3)" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition:  "200% 0" },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "hero-gradient": "linear-gradient(135deg, #101022 0%, #1a1a3e 50%, #101022 100%)",
        "card-gradient": "linear-gradient(135deg, rgba(17,17,212,0.08) 0%, rgba(17,17,212,0.02) 100%)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};

export default config;
