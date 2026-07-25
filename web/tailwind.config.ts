import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "#0f766e",
          foreground: "#ffffff",
        },
        accent: {
          DEFAULT: "#06b6d4",
          foreground: "#ffffff",
        },
      },
    },
  },
  plugins: [],
};

export default config;
