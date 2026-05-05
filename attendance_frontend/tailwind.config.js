/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        candy: {
          pink: '#ff7eb3',
          purple: '#7b4397',
          blue: '#4facfe',
          cyan: '#00f2fe'
        }
      }
    },
  },
  plugins: [],
}