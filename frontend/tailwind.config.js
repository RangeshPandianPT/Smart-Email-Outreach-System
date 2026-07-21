/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-dark': '#0f172a',
        'brand-surface': '#1e293b',
        'brand-accent': '#3b82f6',
      }
    },
  },
  plugins: [],
}
