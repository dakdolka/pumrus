import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
   plugins: [react()],
    server: {
    host: "0.0.0.0",         // чтобы Vite был доступен извне
    port: 3000,
    strictPort: true,
    allowedHosts: ['bestgreen.ru'],
    https: false,             // SSL делаем на Nginx, dev-server работает HTTP
    hmr: false,
    proxy: {
      "/api/": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
})