/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F5F3EE",
        surface: "#FFFFFF",
        line: { DEFAULT: "#E4E0D7", strong: "#CFC9BB" },
        ink: { DEFAULT: "#16181B", 2: "#4B5057", 3: "#858A91" },
        brand: { DEFAULT: "#0E5A52", hover: "#0A443E", soft: "#E3EFEC", deep: "#0B3D38" },
        // Clinical states. Always paired with an icon + label, never colour alone (Invariant 5).
        flag: { DEFAULT: "#B4340F", soft: "#FBE9E2" },
        pending: { DEFAULT: "#8A5A00", soft: "#FBF0D5" },
        ok: { DEFAULT: "#216E45", soft: "#E1F1E7" },
        fix: { DEFAULT: "#2A4E8D", soft: "#E5ECF8" },
      },
      fontFamily: {
        sans: ['"Inter"', "system-ui", "sans-serif"],
        display: ['"Fraunces"', "Georgia", "serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 0 rgba(22,24,27,0.04), 0 1px 2px rgba(22,24,27,0.04)",
        lift: "0 12px 32px -12px rgba(22,24,27,0.18)",
      },
      keyframes: {
        rise: { from: { opacity: 0, transform: "translateY(6px)" }, to: { opacity: 1, transform: "none" } },
        shimmer: { "100%": { transform: "translateX(100%)" } },
      },
      animation: { rise: "rise .4s cubic-bezier(.2,.7,.2,1) both" },
    },
  },
  plugins: [],
};
