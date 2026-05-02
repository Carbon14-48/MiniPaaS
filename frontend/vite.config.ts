import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/auth': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/repos': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/deployments': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/builds': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/metrics': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/logs': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/scanner': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/registry': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
  },
})
