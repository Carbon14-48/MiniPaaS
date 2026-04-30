import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/auth': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/repos': {
        target: 'http://localhost:8008',
        changeOrigin: true,
      },
      '/deployments': {
        target: 'http://localhost:8008',
        changeOrigin: true,
      },
      '/metrics': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
      '/logs': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
    },
  },
})