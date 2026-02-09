/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'ide-bg': '#1e1e1e',
        'ide-sidebar': '#252526',
        'ide-toolbar': '#333333',
        'ide-border': '#3e3e42',
        'ide-text': '#cccccc',
        'ide-accent': '#007acc',
        'ide-warning': '#ffcc00',
        'ide-error': '#f44747',
        'ide-success': '#4ec9b0'
      },
      fontFamily: {
        'mono': ['Consolas', 'Monaco', 'Courier New', 'monospace']
      },
      spacing: {
        'sidebar': '250px',
        'toolbar': '48px',
        'bottom-panel': '200px'
      }
    }
  },
  plugins: []
}