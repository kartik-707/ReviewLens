/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.vite.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        syne:  ["Syne", "sans-serif"],
        mono:  ["DM Mono", "monospace"],
        sans:  ["DM Sans", "sans-serif"],
      },
      colors: {
        ink:     "#0d0d0f",
        paper:   "#f5f3ee",
        accent:  "#c8522a",
        pos:     "#3d6b4f",
        neg:     "#b03a2e",
        gold:    "#b5893a",
        muted:   "#7a7468",
      },
    },
  },
  plugins: [],
};
