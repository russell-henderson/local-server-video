import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        "ink-soft": "#121a2f",
        "ink-glow": "#1f2a44",
        cyan: "#22d3ee",
        "cyan-deep": "#2563eb",
        purple: "#a855f7",
        pink: "#ec4899",
        orange: "#fb923c",
        red: "#ef4444",
        emerald: "#34d399",
        teal: "#14b8a6",
        surface: "rgba(17, 24, 39, 0.72)",
        border: "rgba(148, 163, 184, 0.35)",
      },
      backgroundImage: {
        "brand-cyan": "linear-gradient(135deg, #22d3ee, #2563eb)",
        "brand-purple": "linear-gradient(135deg, #a855f7, #ec4899)",
        "brand-orange": "linear-gradient(135deg, #fb923c, #ef4444)",
        "brand-green": "linear-gradient(135deg, #34d399, #14b8a6)",
        "grid-neon":
          "radial-gradient(circle at 1px 1px, rgba(56,189,248,0.25) 1px, transparent 0)",
      },
      boxShadow: {
        neon: "0 10px 40px rgba(56, 189, 248, 0.25)",
        glass: "0 12px 50px rgba(0, 0, 0, 0.35)",
      },
      dropShadow: {
        glow: "0 0 12px rgba(56, 189, 248, 0.45)",
      },
      borderRadius: {
        xl: "1rem",
      },
    },
  },
  plugins: [],
};

export default config;
