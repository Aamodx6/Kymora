/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "var(--color-canvas)",
        card: "var(--color-card)",
        ink: {
          DEFAULT: "var(--color-ink)",
          pure: "var(--color-ink)",
          soft: "var(--color-body)",
        },
        body: "var(--color-body)",
        muted: "var(--color-muted)",
        subtle: "var(--color-muted)",
        borderLine: "var(--color-border)",
        borderDim: "var(--color-border-dim)",
        highlight: {
          DEFAULT: "var(--color-highlight)",
          alt: "#FFE14D",
        },
      },
      fontFamily: {
        sans: ['"Archivo"', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"Fragment Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'card': '0 0 0 1px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04), 0 28px 56px -28px rgba(0, 0, 0, 0.16)',
        'card-hover': '0 0 0 1.5px rgba(0, 0, 0, 0.14), 0 4px 12px rgba(0, 0, 0, 0.06), 0 32px 64px -24px rgba(0, 0, 0, 0.22)',
        'pop': '0 0 0 1px rgba(0, 0, 0, 0.08), 0 20px 44px -20px rgba(0, 0, 0, 0.24)',
        'btn': '0 1px 2px rgba(0, 0, 0, 0.05)',
      },
      borderRadius: {
        'sm': '4px',
        'md': '6px',
        'lg': '10px',
        'xl': '12px',
      },
      maxWidth: {
        'container': '1248px',
      },
      transitionTimingFunction: {
        'editorial': 'cubic-bezier(0.22, 1, 0.36, 1)',
      }
    },
  },
  plugins: [],
}
