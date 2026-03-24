/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Cormorant Garamond", "serif"],
        body: ["Manrope", "sans-serif"]
      },
      boxShadow: {
        wardrobe: "inset 0 2px 12px rgba(47, 38, 30, 0.08), 0 18px 45px rgba(47, 38, 30, 0.12)"
      }
    }
  },
  plugins: []
};

