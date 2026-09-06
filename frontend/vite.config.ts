import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/verify-document': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/vidyut-assist': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/audit-log': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/verification': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/history': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/stats': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/tampering': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/alerts': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/verifications': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

