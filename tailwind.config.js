/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './*.{ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
      colors: {
        slate: {
          950: '#0f172a',
          900: '#0f1419',
          800: '#1e293b',
          700: '#334155',
          400: '#78716c',
          300: '#cbd5e1',
        },
      },
    },
  },
  plugins: [],
};
