/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        // --- Static brand palettes (theme-independent accents) ---------------
        ink: {
          950: '#070b16', 900: '#0b1020', 850: '#0f1526',
          800: '#151c30', 700: '#1e2740', 600: '#2a3350',
        },
        brand: {
          400: '#5eead4', 500: '#22d3ee', 600: '#0ea5e9', 700: '#4f46e5',
        },
        risk: {
          critical: '#f43f5e', high: '#fb923c', medium: '#fbbf24', low: '#34d399',
        },
        // --- Semantic theme tokens (Day/Night via CSS variables) -------------
        // Each resolves through a CSS custom property so a single class works in
        // both themes; the RGB triple keeps Tailwind's /opacity modifier usable.
        surface: 'rgb(var(--surface) / <alpha-value>)',
        panel: 'rgb(var(--panel) / <alpha-value>)',
        elevated: 'rgb(var(--elevated) / <alpha-value>)',
        hairline: 'rgb(var(--hairline) / <alpha-value>)',
        'hairline-strong': 'rgb(var(--hairline-strong) / <alpha-value>)',
        hover: 'rgb(var(--hover) / <alpha-value>)',
        fg: 'rgb(var(--fg) / <alpha-value>)',
        body: 'rgb(var(--body) / <alpha-value>)',
        muted: 'rgb(var(--muted) / <alpha-value>)',
        subtle: 'rgb(var(--subtle) / <alpha-value>)',
        accent: 'rgb(var(--accent) / <alpha-value>)',
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(79,70,229,0.25), 0 8px 40px -12px rgba(34,211,238,0.25)',
        card: 'var(--card-shadow)',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg,#4f46e5 0%,#0ea5e9 55%,#22d3ee 100%)',
      },
    },
  },
  plugins: [],
}
