tailwind.config = {
  theme: {
    extend: {
      colors: {
        customRed: "rgb(220, 38, 38)",
        customGray: "rgb(75, 85, 99)",
        customWhite: "rgb(245, 245, 245)",
      },
      textShadow: {
        sm: "1px 1px 2px rgba(0, 0, 0, 0.25)",
        DEFAULT: "2px 2px 4px rgba(0, 0, 0, 0.3)", // Default shadow
        lg: "3px 3px 6px rgba(0, 0, 0, 0.4)",
      },
    }
  },
  plugins: [
    function ({ addUtilities }) {
      const newUtilities = {
        ".text-shadow-sm": {
          textShadow: "1px 1px 2px rgba(0, 0, 0, 0.25)",
        },
        ".text-shadow": {
          textShadow: "2px 2px 4px rgba(0, 0, 0, 0.3)",
        },
        ".text-shadow-lg": {
          textShadow: "3px 3px 6px rgba(0, 0, 0, 0.4)",
        },
      };
      addUtilities(newUtilities);
    },
  ],
}