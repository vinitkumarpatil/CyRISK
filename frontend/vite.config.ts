import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The backend runs on :8000 by default. In dev we proxy /api to it so the SPA
// can use same-origin relative URLs; for a deployed build set VITE_API_BASE.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0', // Allow external connections for Docker
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  preview: { port: 4173 },
})
