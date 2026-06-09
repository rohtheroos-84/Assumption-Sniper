module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}", "./pages/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: '#00FF7F',
        bg: '#000000',
        surface: '#0b0b0b',
      },
      fontFamily: {
        sans: ['Inter', 'ui-system', 'system-ui', 'sans-serif'],
      },
      spacing: {
        '72': '18rem',
        '84': '21rem',
        '96': '24rem'
      }
    }
  },
  plugins: [],
}
