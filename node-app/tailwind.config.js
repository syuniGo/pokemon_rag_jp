// tailwind.config.js
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#1a1f36',
        card: '#2a2f45',
        cardHover: '#3a3f55',
        accent: '#4c4dff',
      }
    }
  },
  plugins: [],
}