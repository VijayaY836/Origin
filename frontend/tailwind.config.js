/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#EEF2F6",
        surface: "#FFFFFF",
        sunk: "#F6F8FA",
        line: "#DDE3EA",
        ink: { DEFAULT: "#142033", 2: "#46566A", 3: "#8292A5" },
        mem: { DEFAULT: "#2458E6", soft: "#E7EEFD", mid: "#B9CCF8" },
        warn: { DEFAULT: "#C76A00", soft: "#FDF1E0", mid: "#F5CF9A" },
        ok: { DEFAULT: "#0B8A5F", soft: "#E1F4EC", mid: "#9ED9C1" },
        fault: { DEFAULT: "#D6334A", soft: "#FCEAEC", mid: "#F2B3BD" },
        hs: { DEFAULT: "#6D3FE0", soft: "#EFE9FD" },
      },
      fontFamily: {
        display: ['"Barlow Condensed"', '"Arial Narrow"', "sans-serif"],
        sans: ["Barlow", "system-ui", "sans-serif"],
      },
      boxShadow: { panel: "0 1px 2px rgba(20,32,51,.06)" },
    },
  },
  plugins: [],
};