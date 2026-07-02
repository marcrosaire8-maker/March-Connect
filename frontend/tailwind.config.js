/** @type {import('tailwindcss').Config} */
const brand = {
  DEFAULT: "#1E9E5C",
  dark: "#187A49",
  light: "#3DBB73",
  lighter: "#7AD9A4",
  muted: "#E3F5EB",
  foreground: "#FFFFFF",
  50: "#E8F6EF",
  100: "#D0EDE0",
  200: "#A3DBC1",
  300: "#76C9A2",
  400: "#49B783",
  500: "#2EAB6F",
  600: "#1E9E5C",
  700: "#187A49",
  800: "#125A36",
  900: "#0C3D24",
  950: "#082818",
};

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand,
        green: brand,
        primary: {
          DEFAULT: brand.DEFAULT,
          dark: brand.dark,
          light: brand.light,
          foreground: brand.foreground,
        },
        accent: {
          DEFAULT: "#D97706",
          light: "#F59E0B",
          dark: "#B45309",
          foreground: "#0F1E3D",
        },
        surface: {
          DEFAULT: "#faf8f4",
          card: "#FFFFFF",
          muted: "#f3f1ec",
        },
        neutral: {
          50: "#FAFAF9",
          100: "#F5F5F4",
          200: "#E7E5E4",
          300: "#D6D3D1",
          400: "#A8A29E",
          500: "#78716C",
          600: "#57534E",
          700: "#44403C",
          800: "#292524",
          900: "#1C1917",
        },
        success: {
          DEFAULT: brand.DEFAULT,
          light: brand.muted,
        },
        danger: {
          DEFAULT: "#DC2626",
          light: "#FEE2E2",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      fontSize: {
        display: ["2.25rem", { lineHeight: "2.5rem", fontWeight: "700" }],
        h1: ["1.875rem", { lineHeight: "2.25rem", fontWeight: "700" }],
        h2: ["1.5rem", { lineHeight: "2rem", fontWeight: "600" }],
        h3: ["1.25rem", { lineHeight: "1.75rem", fontWeight: "600" }],
        body: ["1rem", { lineHeight: "1.5rem", fontWeight: "400" }],
        "body-sm": ["0.875rem", { lineHeight: "1.25rem", fontWeight: "400" }],
        caption: ["0.75rem", { lineHeight: "1rem", fontWeight: "500" }],
      },
      boxShadow: {
        card: "0 2px 16px -2px rgb(30 158 92 / 0.06), 0 8px 24px -4px rgb(0 0 0 / 0.04)",
        "card-hover":
          "0 8px 30px -6px rgb(30 158 92 / 0.12), 0 4px 12px -2px rgb(0 0 0 / 0.06)",
        dashboard: "0 4px 32px -8px rgb(30 158 92 / 0.1), 0 16px 48px -16px rgb(0 0 0 / 0.08)",
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      ringOffsetColor: {
        DEFAULT: "#FAFAF9",
      },
    },
  },
  plugins: [],
};
