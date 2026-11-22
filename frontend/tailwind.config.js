/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        display: ["Manrope", "Inter", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#f0fdfa",
          100: "#ccfbf1",
          200: "#99f6e4",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
          900: "#134e4a",
          950: "#042f2e",
        },
      },
      keyframes: {
        "fade-slide-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "stamp-in": {
          "0%": { opacity: "0", transform: "scale(1.35) rotate(-12deg)" },
          "70%": { opacity: "1", transform: "scale(0.96) rotate(-4deg)" },
          "100%": { opacity: "1", transform: "scale(1) rotate(-6deg)" },
        },
        "sheet-pulse": {
          "0%, 100%": { boxShadow: "0 10px 30px -10px rgba(13, 148, 136, 0.16)" },
          "50%": { boxShadow: "0 16px 36px -8px rgba(13, 148, 136, 0.28)" },
        },
      },
      animation: {
        "fade-slide-up": "fade-slide-up 240ms cubic-bezier(0.16, 1, 0.3, 1) both",
        "stamp-in": "stamp-in 420ms cubic-bezier(0.16, 1, 0.3, 1) both",
        "sheet-pulse": "sheet-pulse 2.2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
