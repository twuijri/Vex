import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

// The SPA is served by FastAPI under /dashboard, so assets resolve from
// /dashboard/assets. Build output goes to ../web/spa (copied into the image).
export default defineConfig({
  plugins: [react()],
  base: '/dashboard/',
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: process.env.VEX_DEV_API || 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../web/spa',
    emptyOutDir: true,
  },
})
