/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Oracle cosmic palette — only these colours are permitted
        cosmic: {
          bg: '#050510',
          'bg-secondary': '#0a0a1a',
          'bg-card': '#0d0d20',
          'bg-elevated': '#12122a',
          cyan: '#00D4FF',
          'cyan-dim': '#0099bb',
          'cyan-glow': 'rgba(0, 212, 255, 0.15)',
          amber: '#FFB800',
          'amber-dim': '#cc9200',
          'amber-glow': 'rgba(255, 184, 0, 0.15)',
          red: '#FF3B30',
          'red-dim': '#cc2f26',
          'red-glow': 'rgba(255, 59, 48, 0.15)',
          green: '#34C759',
          'green-dim': '#28a046',
          purple: '#BF5AF2',
          'text-primary': '#E8E8F0',
          'text-secondary': '#8888aa',
          'text-muted': '#555570',
          border: 'rgba(255, 255, 255, 0.08)',
          'border-bright': 'rgba(0, 212, 255, 0.3)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 8s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          from: { boxShadow: '0 0 10px rgba(0, 212, 255, 0.3)' },
          to: { boxShadow: '0 0 25px rgba(0, 212, 255, 0.7)' },
        },
      },
      backgroundImage: {
        'cosmic-gradient': 'radial-gradient(ellipse at center, #0a0a2e 0%, #050510 70%)',
        'card-gradient': 'linear-gradient(135deg, rgba(13,13,32,0.9) 0%, rgba(10,10,26,0.95) 100%)',
        'cyan-gradient': 'linear-gradient(135deg, #00D4FF 0%, #0099bb 100%)',
        'danger-gradient': 'linear-gradient(135deg, #FF3B30 0%, #cc2f26 100%)',
      },
      boxShadow: {
        'cyan-glow': '0 0 20px rgba(0, 212, 255, 0.4)',
        'amber-glow': '0 0 20px rgba(255, 184, 0, 0.4)',
        'red-glow': '0 0 20px rgba(255, 59, 48, 0.4)',
        'card': '0 4px 24px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [],
}
