/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        rl: {
          // Ink - primary text
          ink: '#0F1512',
          
          // Action Green
          green: {
            50:  '#f0fdf4',
            100: '#dcfce7',
            200: '#bbf7d0',
            300: '#86efac',
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d',
            800: '#166534',
            900: '#14532d',
          },
          // AI Amber / Proposed
          amber: {
            50:  '#FFFAF0',
            100: '#FEF0C7',
            200: '#FDE08B',
            500: '#F59E0B',
            600: '#D97706',
            700: '#B45309',
          },
          // Verified Blue / Database-backed
          blue: {
            50:  '#F0F4FF',
            100: '#E0E7FF',
            200: '#C7D2FE',
            500: '#6366F1',
            600: '#4F46E5',
            700: '#4338CA',
          },
          red: {
            50:  '#fef2f2',
            100: '#fee2e2',
            500: '#ef4444',
            600: '#dc2626',
            700: '#b91c1c',
          },
          // Warm Neutrals
          neutral: {
            50:  '#FAFAF9',
            75:  '#F5F5F4',
            100: '#E7E5E4',
            200: '#D6D3D1',
            300: '#A8A29E',
            400: '#78716C',
            500: '#57534E',
            600: '#44403C',
            700: '#292524',
            800: '#1C1917',
            900: '#0C0A09',
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },
      boxShadow: {
        'rl-sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'rl': '0 1px 3px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
        'rl-md': '0 4px 6px -1px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.06)',
        'rl-lg': '0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.06)',
        'rl-drawer': '-8px 0 30px 0 rgb(0 0 0 / 0.12)',
      },
      borderRadius: {
        'rl': '6px',
        'rl-md': '8px',
        'rl-lg': '12px',
      },
      animation: {
        'slide-in-right': 'slideInRight 0.2s ease-out',
        'fade-in': 'fadeIn 0.15s ease-out',
        'spin-slow': 'spin 2s linear infinite',
        'pulse-subtle': 'pulseSubtle 2s ease-in-out infinite',
      },
      keyframes: {
        slideInRight: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
      },
    },
  },
  plugins: [],
}
