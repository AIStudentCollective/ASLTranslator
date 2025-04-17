import type { Config } from "tailwindcss";

export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: "#2563eb", 
        secondary: "#9333ea", 
        accent: "#f97316",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["Fira Code", "monospace"],
        poppins: ["Poppins", "sans-serif"], 
      },
      spacing: {
        "128": "32rem",
        "144": "36rem",
      },
      borderRadius: {
        xl: "1.5rem",
        "2xl": "2rem",
      },
      boxShadow: {
        soft: "0 4px 6px rgba(0, 0, 0, 0.1)",
        strong: "0 10px 20px rgba(0, 0, 0, 0.2)",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        bounceSlow: {
          "0%, 100%": { transform: "translateY(-10px)" },
          "50%": { transform: "translateY(0px)" },
        },
      },
      animation: {
        fadeIn: "fadeIn 0.5s ease-in-out",
        bounceSlow: "bounceSlow 2s infinite",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"), 
    require("@tailwindcss/typography"), 
    require("@tailwindcss/aspect-ratio"), 
  ],
  darkMode: "class", 
} satisfies Config;
