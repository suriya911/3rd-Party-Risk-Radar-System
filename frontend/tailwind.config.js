/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        radar: {
          bg: "#0f1117",
          card: "#1a1d2e",
          border: "#2d3148",
          accent: "#4f6ef7",
        },
      },
    },
  },
  plugins: [],
};
